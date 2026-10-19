"""Keep the direct matrix definition readable as an executable specification."""

import numpy as np
from numpy.typing import NDArray

import alternative

from .model import rotation, validate


@alternative.reference
def layer_trace(angles: tuple[float, ...], repeats: int = 1) -> complex:
    """Return the trace after repeating a layer of independent qubit rotations."""
    validate(angles, repeats)
    layer: NDArray[np.complexfloating] = np.eye(1, dtype=np.complex128)
    for angle in angles:
        layer = np.kron(layer, rotation(angle))
    return complex(np.trace(np.linalg.matrix_power(layer, repeats)))
