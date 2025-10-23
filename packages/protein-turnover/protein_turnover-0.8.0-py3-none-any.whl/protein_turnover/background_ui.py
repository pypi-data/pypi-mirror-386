from __future__ import annotations

import sys

import click

from .cli import cli
from .cli import Config
from .cli import pass_config


@cli.command(name="background")
@click.option(
    "--workers",
    type=int,
    help="number of workers [default - half the number of cpus]",
)
@click.option(
    "--nice",
    default=0,
    type=click.IntRange(
        min=0,
    ),
    help="run turnover command at this nice level",
)
@click.option(
    "--sleep",
    default=10.0
    if sys.platform == "win32"
    else 60.0,  # no signal for windows so shorter cycle
    help="sleep (seconds) between directory scans",
    show_default=True,
)
@click.option(
    "--run-config",
    type=click.Path(file_okay=True, dir_okay=False, exists=True),
    help="configuration file to pass off to the background process",
)
@click.option(
    "--compress-result",
    is_flag=True,
    help="compress the resultant sqlite file to save space",
)
@click.option(
    "--mailhost",
    help='send emails to this mailhost. use "none" for no emails',
    hidden=False,
)  # see runner.py
@click.argument(
    "jobs_directory",
    type=click.Path(dir_okay=True, exists=True, file_okay=False),
    required=True,
    nargs=-1,
)
@pass_config
def background_cmd(
    cfg: Config,
    jobs_directory: tuple[str, ...],
    workers: int | None,
    run_config: str | None,
    sleep: float,
    nice: int,
    mailhost: str | None = None,
    compress_result: bool = False,
) -> None:  # pragma: no cover
    """Watch and run turnover jobs from directory"""
    from os import cpu_count
    from .background import SimpleQueue
    from .logger import logger

    if workers is None:
        workers = max((cpu_count() or 1) // 2, 1)
        logger.warning("using %d workers", workers)

    squeue = SimpleQueue(
        jobs_directory,
        workers=workers,
        wait=sleep,
        nice=nice,
        config=run_config or cfg.user_config,
        mailhost=mailhost,
        compress_result=compress_result,
    )
    squeue.run()
