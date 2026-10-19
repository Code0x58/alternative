"""Rank a fixed search population while keeping invalid candidates last."""

from collections.abc import Callable
from math import inf, sqrt

import numpy as np
from numpy.typing import NDArray

import alternative

Circuit = tuple[str, ...]
GATES = {
    "H": np.array([[1, 1], [1, -1]], dtype=np.complex128) / sqrt(2),
    "X": np.array([[0, 1], [1, 0]], dtype=np.complex128),
    "Z": np.array([[1, 0], [0, -1]], dtype=np.complex128),
}


@alternative.reference
def synthesise_x() -> Circuit:
    """Keep the readable identity H Z H = X as the reference circuit."""
    return ("H", "Z", "H")


@synthesise_x.add
def direct_x() -> Circuit:
    """Use one primitive gate with the same unitary action."""
    return ("X",)


@synthesise_x.add
def wrong_x() -> Circuit:
    """Represent a generated candidate with the wrong action."""
    return ("Z",)


@synthesise_x.add
def broken_x() -> Circuit:
    """Represent a generator that cannot construct its proposed circuit."""
    raise ValueError("invalid generated circuit")


def simulate(program: Circuit) -> NDArray[np.complex128]:
    """Simulate a bounded sequence of H, X, and Z gates in execution order."""
    if len(program) > 16:
        raise ValueError("the search demo limits circuits to sixteen gates")
    result = np.eye(2, dtype=np.complex128)
    for name in program:
        result = GATES[name] @ result
    return result


def score_candidate(build: Callable[[], Circuit]) -> float:
    """Minimise gate count, assigning infinity to invalid candidate attempts."""
    try:
        program = build()
        actual = simulate(program)
    except (ArithmeticError, KeyError, ValueError):
        return inf
    if not np.allclose(actual, GATES["X"], rtol=0, atol=1e-12):
        return inf
    return float(len(program))


def rank_candidates() -> dict[str, float]:
    """Score the complete population without changing the runtime default."""
    if not np.allclose(
        simulate(synthesise_x.reference()), GATES["X"], rtol=0, atol=1e-12
    ):
        raise ValueError("reference circuit failed validation")
    scores = {
        implementation.__name__: score_candidate(implementation)
        for implementation in synthesise_x.implementations
    }
    return dict(sorted(scores.items(), key=lambda item: item[1]))
