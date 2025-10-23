from __future__ import annotations

from typing import Callable
from typing import TYPE_CHECKING

import numpy as np
from scipy.fft import fft
from scipy.fft import ifft

from .utils import ATOMICPROPERTIES
from .utils import NAMES
from .utils import PeptideInfo
from .utils import PeptideSettings

if TYPE_CHECKING:
    from .types.numpytypes import NP1DF64Array, NP2DF64Array, NP1DF32Array


def isotopic_distribution(
    pepinfo: PeptideInfo,
    abundance: float | None = None,
    abundanceCutoff: float = 1e-10,
    maxMass: int = 100,
) -> NP1DF64Array:
    # pragma: no cover
    """return abundance of "heavy" peptides"""
    if abundance is None:
        ab = pepinfo.naturalAtomicAbundances
    else:
        ab = pepinfo.labelledAtomicAbundances(abundance)

    abundances = {pepinfo.settings.labelledElement: ab}

    formula = pepinfo.formula

    maxElements = np.sum(formula > 0, dtype=int)

    A = np.zeros((maxElements, maxMass), np.float64)

    elements = []
    for i, e in enumerate(NAMES):
        n = formula[i]
        if n > 0:
            elements.append(n)
            if e in abundances:
                a = abundances[e]
            else:
                # use natural abundance
                a = ATOMICPROPERTIES[e]["abundance"]
            A[len(elements) - 1, 0 : len(a)] = a

    tA = fft(A)

    ptA = np.ones((maxMass,), dtype=np.complex128)

    for i in range(maxElements):
        ptA *= tA[i] ** elements[i]

    riptA = np.real(ifft(ptA))  # type: ignore
    mx = np.max(np.where(riptA > abundanceCutoff))
    riptA = riptA[0 : int(mx) + 1]
    return np.fmax(riptA, 0.0)
    # return np.where(riptA > 0.0, riptA, 0.0)


def isotopic_distributionR(
    pepinfo: PeptideInfo,
    abundance: float | None = None,
    abundanceCutoff: float = 1e-10,
    maxMass: int = 100,
) -> NP1DF64Array:
    # pragma: no cover
    """return abundance of "heavy" peptides"""
    if abundance is None:
        ab = pepinfo.naturalAtomicAbundances
    else:
        ab = pepinfo.labelledAtomicAbundances(abundance)

    abundances = {pepinfo.settings.labelledElement: ab}

    formula = pepinfo.formula

    maxElements = np.sum(formula > 0, dtype=int)

    A = np.zeros((maxElements, maxMass), np.complex64)

    elements = []
    for i, e in enumerate(NAMES):
        n = formula[i]
        if n > 0:
            elements.append(n)
            if e in abundances:
                a = abundances[e]
            else:
                # use natural abundance
                a = ATOMICPROPERTIES[e]["abundance"]
            A[len(elements) - 1, 0 : len(a)] = a

            A[len(elements) - 1, :] = fft(A[len(elements) - 1, :], maxMass)[:maxMass]  # type: ignore

    tA = A

    ptA = np.ones((maxMass,), dtype=np.complex128)

    for i in range(maxElements):
        ptA *= tA[i] ** elements[i]

    riptA = np.real(ifft(ptA))  # type: ignore
    mx = np.max(np.where(riptA > abundanceCutoff))
    riptA = riptA[0 : int(mx) + 1]
    return np.fmax(riptA, 0.0)


def mk_maxIso(settings: PeptideSettings) -> Callable[[str], np.int32]:
    # pragma: no cover
    from .config import ABUNDANCE_CUTOFF

    def maxIso(peptide: str) -> np.int32:
        pepinfo = PeptideInfo(peptide, settings)
        r = isotopic_distribution(
            pepinfo,
            settings.maximumLabelEnrichment,
            abundanceCutoff=ABUNDANCE_CUTOFF,
        )
        return np.int32(len(r) - 1)

    return maxIso


def make_envelope_array(
    pepinfo: PeptideInfo,
    maxIso: int,
) -> tuple[NP1DF64Array, NP2DF64Array]:
    # enrichments = pepinfo.getEnrichments(maxIso)
    enrichments = pepinfo.settings.getEnrichmentsN(pepinfo.elementCount)

    isotope_envelope_basis = np.zeros(
        shape=(maxIso + 1, len(enrichments)),
        dtype=np.float64,
    )
    for i, element_enrichment_level in enumerate(enrichments):
        d = isotopic_distribution(pepinfo, element_enrichment_level)
        max_el = min(len(d), maxIso + 1)
        isotope_envelope_basis[:max_el, i] = d[:max_el]
    return enrichments, isotope_envelope_basis


def natural_dist(
    pepinfo: PeptideInfo,
    monoScale: float,
) -> NP1DF32Array:
    isod = isotopic_distribution(pepinfo)
    denom = isod[0]
    denom = denom if denom > 0.0 else 1.0
    return (monoScale * isod / denom).astype(np.float32)
