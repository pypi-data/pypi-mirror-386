from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
import tomllib
from datetime import datetime
from pathlib import Path
from shutil import rmtree
from shutil import which
from typing import Any
from typing import Iterator
from typing import Sequence

import tomli_w
from typing_extensions import override

from .logger import logger

try:
    from psutil import pid_exists  # type: ignore

    psutil_ok = True  # pragma: no cover
except ImportError:
    psutil_ok = False

    # for windows we need psutil.pid_exists(pid)
    def pid_exists(pid: int) -> bool:  # pragma: no cover
        """Check whether pid exists in the current process table Unix Only."""
        if pid == 0:
            # According to "man 2 kill" PID 0 has a special meaning:
            # it refers to <<every process in the process group of the
            # calling process>> so we don't want to go any further.
            # If we get here it means this UNIX platform *does* have
            # a process with id 0.
            return True
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            # EPERM clearly means there's a process to deny access to
            return True
        # According to "man 2 kill" possible error values are
        # (EINVAL, EPERM, ESRCH)
        else:
            return True


# see https://stackoverflow.com/questions/35772001/how-to-handle-a-signal-sigint-on-a-windows-os-machine


# from https://stackoverflow.com/questions/18499497/how-to-process-sigterm-signal-gracefully
# class GracefulKiller:
#     kill_now: bool = False

#     def __init__(self) -> None:
#         self.kill_now: bool = False
#         self.old: Any = None

#     def __enter__(self) -> None:
#         self.old = signal.signal(signal.SIGTERM, self.exit_gracefully)

#     def __exit__(self, *args: Any) -> None:
#         if self.old is not None:
#             signal.signal(signal.SIGTERM, self.old)
#             self.old = None
#         if self.kill_now:
#             raise ContinueException()

#     def exit_gracefully(self, *args: Any) -> None:
#         self.kill_now = True


class ContinueException(Exception):
    pass


class Handler:
    def __init__(self, processing: bool = True):
        self.processing = processing

    def __call__(self, signum: int, frame: Any) -> None:  # pragma: no cover
        if self.processing:
            return
        raise ContinueException()

    def arm(self) -> None:  # pragma: no cover
        if sys.platform == "win32":
            return
        signal.signal(signal.SIGCONT, self)


PID_FILENAME = "turnover.pid"
PROCESSING = "turnover.pid.is_running"


class Processing:
    """Is the background worker processing a job ATM?"""

    def __init__(self, jobsdir: Path):
        self._processing = jobsdir.joinpath(PROCESSING)

    def is_processing(self) -> bool:
        return self._processing.exists()

    def set_processing(self, start: bool) -> None:
        if start:
            self._processing.touch()
        else:
            try:
                self._processing.unlink(missing_ok=True)
            except OSError:  # pragma: no cover
                pass


## @export
class SimpleQueueClient:
    """Used by web client to interact with background Queue.

    Currently only just sends a signal to wake up.
    """

    def __init__(self, jobdir: Path) -> None:
        self.jobdir = jobdir
        self.pidfile = jobdir.joinpath(PID_FILENAME)

    def terminate(self) -> bool:  # pragma: no cover
        pid = self.get_pid()
        if pid is None:
            return False
        try:
            os.kill(pid, signal.SIGINT)
        except ProcessLookupError:
            return False
        except PermissionError:
            return False
        return True

    def signal(self) -> bool:  # pragma: no cover
        pid = self.get_pid()
        if pid is None:
            return False
        self.pidfile.touch()
        if sys.platform == "win32":
            return False
        try:
            os.kill(pid, signal.SIGCONT)
        except ProcessLookupError:
            return False
        except PermissionError:
            return False
        return True

    def is_running(self) -> bool:
        pid = self.get_pid()
        if pid is None:
            return False
        return self._pid_exists(pid)

    def get_pid(self) -> int | None:
        if self.pidfile.exists():
            with self.pidfile.open("r") as fp:
                try:
                    return int(fp.read())
                except (TypeError, OSError):  # pragma: no cover
                    return None
        return None  # pragma: no cover

    def _pid_exists(self, pid: int) -> bool:
        return pid_exists(pid)


def remove_old_sqlite(root_list: list[Path], seconds: float) -> int:
    """Remove any "old" .sqlite files but only if there is a .gz file
    next to it. This is used to save space when --compress-result is used."""
    from .exts import RESULT_EXT

    now = datetime.now().timestamp()
    n = 0
    for root in root_list:
        for d, _, files in root.walk():
            for f in files:
                if f.endswith(RESULT_EXT):
                    sqlite = d / f
                    sqlitegz = sqlite.with_suffix(sqlite.suffix + ".gz")
                    # if this is a symlink then *assume* the target is there
                    # on network filesystem
                    if not sqlitegz.exists(follow_symlinks=False):
                        continue
                    if not sqlite.exists(
                        follow_symlinks=True,
                    ):  # sqlite might be symlink
                        continue
                    delta = now - sqlite.stat(follow_symlinks=True).st_mtime
                    # older than seconds
                    if delta > seconds:
                        try:
                            # remove underlying file
                            rf = sqlite.resolve()
                            rf.unlink(missing_ok=True)
                            logger.info('removed old sqlite file "%s"', rf)
                            n += 1
                        except OSError:
                            pass
    return n


class SimpleQueue:
    INTERROR = 22

    def __init__(
        self,
        jobdirs: Sequence[str | Path] | str | Path,
        wait: float = 60,
        workers: int = 4,
        nice: int = 0,
        config: str | None = None,
        mailhost: str | None = None,
        compress_result: bool = False,
    ) -> None:
        if isinstance(jobdirs, (str, Path)):
            jobdirs = [jobdirs]
        assert len(jobdirs) > 0, "must have at least one job directory"
        self.jobsdirs = list(Path(d) for d in jobdirs)

        self.jobdir = self.jobsdirs[0]
        self.wait = wait
        self.workers = workers
        self.nice = nice
        self.mailhost = mailhost
        self.compress_result = compress_result
        self.nice_cmd = which("nice")
        self.handler = Handler()
        if config is not None:
            if not os.path.exists(config):  # pragma: no cover
                logger.warning(
                    "configuration file %s doesn't exist! ignoring...",
                    config,
                )
                config = None
        self.config = config
        self.processing = Processing(self.jobdir)

        self.quit = False  # only for testing
        self.arm_signals()

    def arm_signals(self) -> None:  # pragma: no cover
        self.handler.arm()

    def start_cleanup(self) -> None:
        """scan jobdir and remove any .sqlite files older than age seconds
        but only if there is a .gz file next to it. This runs in a separate thread.
        """
        from threading import Thread
        from .config import COMPRESS_AGE, COMPRESS_SLEEP

        def cleanup() -> None:
            while True:
                remove_old_sqlite(self.jobsdirs, seconds=COMPRESS_AGE)
                time.sleep(COMPRESS_SLEEP)

        tr = Thread(target=cleanup, daemon=True)
        tr.start()

    def command(self, *args: str) -> list[str]:  # pragma: no cover
        nice = []
        if self.nice_cmd and self.nice:
            nice = [self.nice_cmd, "-n", str(self.nice)]

        config = [f"--config={self.config}"] if self.config is not None else []

        email = [f"--mailhost={self.mailhost}"] if self.mailhost else []
        if self.compress_result:
            email.append("--compress-result")

        return [
            *nice,
            sys.executable,
            "-m",
            "protein_turnover",
            *config,
            "run",
            f"--interrupt-as-error={self.INTERROR}",
            f"--workers={self.workers}",
            *email,
            *args,
        ]

    def pidfile(self, tomlfile: Path) -> Path:
        return tomlfile.parent.joinpath(tomlfile.name + ".pid")

    def rmlog(self, tomlfile: Path) -> None:
        lf = tomlfile.parent.joinpath(tomlfile.stem + ".log")
        lf.unlink(missing_ok=True)

    def runjobs(self, it: Iterator[Path]) -> None:
        for tomlfile in it:
            self.rmlog(tomlfile)
            cmd = self.command(str(tomlfile))
            with subprocess.Popen(
                cmd,
                shell=False,
                text=True,
            ) as proc:
                try:
                    # logger.info("%s: running pid=%d", tomlfile, proc.pid)
                    logger.info("running[%s]: %s", proc.pid, cmd)
                    # let website know that this job is running....
                    # see SimpleQueueClient
                    pid = self.pidfile(tomlfile)
                    with pid.open("w") as fp:
                        fp.write(str(proc.pid))
                    self.processing.set_processing(True)
                    try:
                        _, errs = proc.communicate()
                        if errs:
                            logger.error("error from %s: %s", tomlfile, errs)
                        ret = proc.wait()  # TODO what happens when we're terminated?
                    finally:  # can catch KeyboardInterrupt
                        pid.unlink(missing_ok=True)
                        self.processing.set_processing(False)
                    if ret < 0:  # pragma: no cover
                        if -ret in {signal.SIGTERM, signal.SIGKILL}:
                            logger.warning("%s: killed...", tomlfile)
                    status = (
                        "finished"
                        if ret == 0
                        else ("killed" if ret < 0 or ret == self.INTERROR else "failed")
                    )
                    logger.info("%s: status=%s", tomlfile, status)
                    try:
                        self.update_status(tomlfile, status)
                    except Exception as e:  # pragma: no cover
                        logger.error("can't update status! %s: %s", tomlfile, e)
                except KeyboardInterrupt:  # pragma: no cover
                    logger.info("sending signal to child process")
                    if sys.platform == "win32":
                        proc.terminate()
                        rmtree(tomlfile.parent, ignore_errors=True)
                    else:
                        proc.send_signal(signal.SIGINT)
                    try:
                        proc.wait(1.0)
                    except subprocess.TimeoutExpired:
                        pass

    def update_status(self, tomlfile: Path, status: str) -> None:
        c = self.read_toml(tomlfile)
        if c is None:  # pragma: no cover
            return
        c["status"] = status
        if status in {"finished", "killed", "failed"}:
            c["finished_time"] = datetime.now()
        with tomlfile.open("wb") as fp:
            tomli_w.dump(c, fp)

    def read_toml(self, tomlfile: Path) -> dict[str, Any] | None:
        try:
            with tomlfile.open("rb") as fp:
                return tomllib.load(fp)
        except Exception as e:  # pragma: no cover
            logger.error("can't open %s: %s", tomlfile, e)
            return None

    def status(self, tomlfile: Path) -> str:
        c = self.read_toml(tomlfile)
        if c is None:  # pragma: no cover
            return "failed"
        return str(c.get("status", "stopped"))

    def search(self, directory: Path, wait: float = 60.0) -> Iterator[Path]:
        nloop = 0
        mtime = None
        todo: list[tuple[Path, float]] = []
        every = max(60 * int(60 / wait), 1) if wait else 1  # each hour
        while True:
            if (nloop % every) == 0:
                logger.info("searching for jobs in %s", directory.absolute())
            nloop += 1
            last = self.mtime()
            for d, _, files in directory.walk():
                for f in files:
                    if f.endswith(".toml"):
                        tomlfile = d / f
                        # already running
                        if self.pidfile(tomlfile).exists():
                            continue
                        mod = tomlfile.stat().st_mtime
                        if mtime is None or mod > mtime:
                            try:
                                if self.status(tomlfile) == "pending":
                                    todo.append((tomlfile, mod))
                            except Exception as e:  # pragma: no cover
                                logger.error("%s: %s", tomlfile, e)

            if todo:
                n = len(todo)
                logger.info("found %d job%s", n, "" if n == 1 else "s")
                todo = sorted(todo, key=lambda t: t[1])  # oldest first
                for tomlfile, m in todo:
                    if tomlfile.exists():
                        mtime = m
                        yield tomlfile
                todo = []
            try:
                # when we are signaled by website with signal.SIGCONT
                # the self.handler will throw a ContinueException
                # but only if processing is False
                # otherwise it will eat the signal
                self.handler.processing = False
                for _ in range(20):
                    if self.quit:
                        return
                    time.sleep(wait)
                    latest = self.mtime()
                    if latest > last:
                        break
            except ContinueException:  # pragma: no cover
                # kill -CONT $(cat {pidfile})
                logger.info("awakened by signal....")
            finally:
                self.handler.processing = True

    def mtime(self):
        pidfile = self.thispid()
        return pidfile.stat().st_mtime

    def thispid(self) -> Path:
        return self.jobdir.joinpath(PID_FILENAME)

    def process(self, jobdir: Path, wait: float = 60.0) -> None:
        self.runjobs(self.search(jobdir, wait))

    def run(self) -> None:
        if self.compress_result:
            self.start_cleanup()
        pidfile = self.thispid()
        try:
            with pidfile.open("wt", encoding="utf-8") as fp:
                pid = os.getpid()
                fp.write(str(pid))
            w = "with 👍" if psutil_ok else "without 👎"
            print(f"protein_turnover queue running ({w} psutil) as pid={pid}")
            self.process(self.jobdir, self.wait)
        finally:
            pidfile.unlink(missing_ok=True)


class TestSimpleQueue(SimpleQueue):
    @override
    def arm_signals(self) -> None:
        pass

    @override
    def command(self, *args: str) -> list[str]:
        return [sys.executable, "-m", "protein_turnover.background", *args]


if __name__ == "__main__":
    # used in testing....
    import click

    @click.command()
    @click.argument("jobfile")
    def testrun(jobfile: str):
        """Minimal job run"""
        tomlfile = Path(jobfile)
        with tomlfile.open("rb") as fp:
            tf = tomllib.load(fp)

        time.sleep(0.5)  # do some computation :)
        tf["data"] = "done"
        with tomlfile.open("wb") as fp:
            tf = tomli_w.dump(tf, fp)

    testrun()
