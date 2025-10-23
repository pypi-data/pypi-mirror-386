from __future__ import annotations

from typing import TypeAlias
from typing import TypeVar

import numpy as np

Number = TypeVar("Number", bound=np.number)

NP1DF64Array: TypeAlias = np.ndarray[tuple[int], np.dtype[np.float64]]
NP2DF64Array: TypeAlias = np.ndarray[tuple[int, int], np.dtype[np.float64]]
NP1DF32Array: TypeAlias = np.ndarray[tuple[int], np.dtype[np.float32]]
NP1DI32Array: TypeAlias = np.ndarray[tuple[int], np.dtype[np.int32]]
NP2DF32Array: TypeAlias = np.ndarray[tuple[int, int], np.dtype[np.float32]]
NP1DFArray: TypeAlias = np.ndarray[tuple[int], np.dtype[np.floating]]

NP3DF32Array: TypeAlias = np.ndarray[tuple[int, int, int], np.dtype[np.float32]]

NP1DNArray: TypeAlias = np.ndarray[tuple[int], np.dtype[Number]]
