"""Define a bounded, reproducible model of independent single-qubit rotations."""

from math import cos, isfinite, pi, sin, sqrt

import numpy as np
from numpy.typing import NDArray

# The Pauli operator along (1, 1, 1) / sqrt(3); its square is the identity.
AXIS = np.array([[1, 1 - 1j], [1 + 1j, -1]], dtype=np.complex128) / sqrt(3)


def validate(angles: tuple[float, ...], repeats: int) -> None:
    """Keep the dense oracle affordable and floating-point comparisons bounded."""
    if len(angles) > 8:
        raise ValueError("the demo supports at most eight qubits")
    if any(not isfinite(angle) or abs(angle) > pi for angle in angles):
        raise ValueError("angles must be finite and between -pi and pi")
    if not isinstance(repeats, int) or not -16 <= repeats <= 16:
        raise ValueError("repeats must be an integer between -16 and 16")


def rotation(angle: float) -> NDArray[np.complex128]:
    """Return exp(-i angle AXIS / 2), an SU(2) rotation about a fixed unit axis."""
    return cos(angle / 2) * np.eye(2, dtype=np.complex128) - 1j * sin(angle / 2) * AXIS
