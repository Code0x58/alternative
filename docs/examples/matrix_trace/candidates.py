"""Replace large matrices with tensor identities, then with SU(2) characters."""

from math import cos, prod

import numpy as np

from .model import rotation, validate
from .reference import layer_trace


@layer_trace.add
def trace_factorized(angles: tuple[float, ...], repeats: int = 1) -> complex:
    """Distribute powers and traces over the independent tensor factors."""
    validate(angles, repeats)
    return prod(
        (
            complex(np.trace(np.linalg.matrix_power(rotation(angle), repeats)))
            for angle in angles
        ),
        start=1 + 0j,
    )


@layer_trace.add(default=True)
def trace_characters(angles: tuple[float, ...], repeats: int = 1) -> complex:
    """Evaluate each SU(2) character directly from its eigenphases."""
    validate(angles, repeats)
    return complex(prod(2 * cos(repeats * angle / 2) for angle in angles))
