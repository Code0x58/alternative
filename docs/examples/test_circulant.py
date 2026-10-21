"""Compare a direct matrix calculation with its Fourier-space identity."""

from math import isfinite

import numpy as np
import pytest
from hypothesis import given
from hypothesis import strategies as st
from threadpoolctl import threadpool_limits

import alternative


def validate(column: tuple[float, ...], power: int) -> None:
    """Bound the demo's matrix size and eigenvalues for stable comparisons."""
    if not 1 <= len(column) <= 512 or not isinstance(power, int) or not 0 <= power <= 8:
        raise ValueError("use 1 to 512 coefficients and an integer power from 0 to 8")
    if not all(isfinite(value) for value in column) or sum(map(abs, column)) > 1:
        raise ValueError("coefficients must be finite with absolute sum at most one")


@alternative.reference
def circulant_trace(column: tuple[float, ...], power: int = 7) -> float:
    """Build the circulant matrix, raise it to a power, and take its trace."""
    validate(column, power)
    indices = np.arange(len(column))
    matrix = np.asarray(column)[(indices[:, None] - indices) % len(column)]
    return float(np.trace(np.linalg.matrix_power(matrix, power)))


@circulant_trace.add(default=True)
def trace_fft(column: tuple[float, ...], power: int = 7) -> float:
    """Use the Fourier eigenvalues to compute the trace without a matrix."""
    validate(column, power)
    return float(np.sum(np.fft.fft(column) ** power).real)


@circulant_trace.pytest_parametrize()
@pytest.mark.parametrize(
    ("column", "power", "expected"),
    [
        ((0.0, 0.0), 0, 2),
        ((0.0, 0.0), 7, 0),
        ((1.0, 0.0, 0.0), 8, 3),
        ((0.0, 1.0, 0.0), 1, 0),
        ((0.0, 1.0, 0.0), 3, 3),
        ((0.25, 0.25, 0.25), 4, 0.75**4),
        ((0.5, 0.25), 2, 0.625),
        ((-0.5,), 3, -0.125),
    ],
)
def test_known_traces(implementation, column, power, expected) -> None:
    """Check zero powers, cyclic shifts, rank-one matrices, and negative eigenvalues."""
    assert implementation(column, power) == pytest.approx(expected, abs=1e-10)


@circulant_trace.pytest_parametrize_pairs()
@given(
    values=st.lists(st.integers(-10, 10), min_size=1, max_size=32),
    power=st.integers(0, 8),
)
def test_equivalent_traces(reference, implementation, values, power) -> None:
    """Compare the FFT identity with dense powers on bounded signed coefficients."""
    scale = 1 + sum(map(abs, values))
    column = tuple(value / scale for value in values)
    assert implementation(column, power) == pytest.approx(
        reference(column, power), rel=1e-10, abs=1e-10
    )


@circulant_trace.pytest_parametrize()
@pytest.mark.parametrize(
    ("column", "power"),
    [
        ((), 1),
        ((0.0,) * 513, 1),
        ((float("nan"),), 1),
        ((1.1,), 1),
        ((0.5,), -1),
        ((0.5,), 1.5),
    ],
)
def test_invalid_domain(implementation, column, power) -> None:
    """Both implementations enforce the small demo's numerical domain."""
    with pytest.raises(ValueError):
        implementation(column, power)


@circulant_trace.pytest_parametrize()
@pytest.mark.parametrize("size", [64, 256, 512])
@pytest.mark.benchmark(group="circulant_trace")
def test_benchmark(benchmark, implementation, size: int) -> None:
    """Time validation, construction, and computation on identical inputs."""
    values = np.random.default_rng(7).uniform(-1, 1, size)
    column = tuple(float(value) for value in values / (1 + np.abs(values).sum()))
    with threadpool_limits(limits=1, user_api="blas"):
        expected = circulant_trace.reference(column, 7)
        result = benchmark.pedantic(
            implementation, args=(column, 7), rounds=9, iterations=1, warmup_rounds=1
        )
    assert result == pytest.approx(expected, rel=1e-10, abs=1e-10)
