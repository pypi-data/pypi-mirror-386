from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from typing import Callable
from typing import TYPE_CHECKING

from . import current_fit
from . import dec2023_fit

if TYPE_CHECKING:
    from .utils import PeptideSettings
    from .utils import PeptideInfo
    import numpy as np
    from .types.numpytypes import NP1DF64Array, NP2DF64Array, NP1DF32Array


class Algo(ABC):
    @staticmethod
    @abstractmethod
    def mk_maxIso(settings: PeptideSettings) -> Callable[[str], np.int32]: ...

    # @staticmethod
    # @abstractmethod
    # def isotopic_distribution(
    #     pepinfo: PeptideInfo, abundance: float | None = None
    # ) -> NP1DF64Array: ...

    @staticmethod
    @abstractmethod
    def make_envelope_array(
        pepinfo: PeptideInfo,
        maxIso: int,
    ) -> tuple[NP1DF64Array, NP2DF64Array]: ...
    @staticmethod
    @abstractmethod
    def natural_dist(
        pepinfo: PeptideInfo,
        monoScale: float,
    ) -> NP1DF32Array: ...


class AlgoLatest(Algo):
    @staticmethod
    def mk_maxIso(settings: current_fit.PeptideSettings) -> Callable[[str], np.int32]:
        return current_fit.mk_maxIso(settings)

    # @staticmethod
    # def isotopic_distribution(
    #     pepinfo: PeptideInfo, abundance: float | None = None
    # ) -> NP1DF64Array:
    #     return current_fit.isotopic_distribution(pepinfo, abundance)

    @staticmethod
    def make_envelope_array(
        pepinfo: PeptideInfo,
        maxIso: int,
    ) -> tuple[NP1DF64Array, NP2DF64Array]:
        return current_fit.make_envelope_array(pepinfo, maxIso)

    @staticmethod
    def natural_dist(
        pepinfo: PeptideInfo,
        monoScale: float,
    ) -> NP1DF32Array:
        return current_fit.natural_dist(pepinfo, monoScale)


class Algo2023(Algo):
    @staticmethod
    def mk_maxIso(settings: current_fit.PeptideSettings) -> Callable[[str], np.int32]:
        return dec2023_fit.mk_maxIso(settings)

    # @staticmethod
    # def isotopic_distribution(
    #     pepinfo: PeptideInfo, abundance: float | None = None
    # ) -> NP1DF64Array:
    #     return dec2023_fit.isotopic_distribution(pepinfo, abundance)

    @staticmethod
    def make_envelope_array(
        pepinfo: PeptideInfo,
        maxIso: int,
    ) -> tuple[NP1DF64Array, NP2DF64Array]:
        return dec2023_fit.make_envelope_array(pepinfo, maxIso)

    @staticmethod
    def natural_dist(
        pepinfo: PeptideInfo,
        monoScale: float,
    ) -> NP1DF32Array:
        return dec2023_fit.natural_dist(pepinfo, monoScale)


ALGO: dict[str, type[Algo]] = {
    "Latest": AlgoLatest,
    "2023": Algo2023,
}


def settings_to_algo(settings: PeptideSettings) -> type[Algo]:
    return ALGO[settings.pipelineAlgo]
