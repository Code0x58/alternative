"""Compare a direct matrix calculation with its Fourier-space identity."""

import numpy as np
import pytest
from hypothesis import given
from hypothesis import strategies as st
from threadpoolctl import threadpool_limits

import alternative


@alternative.reference
def circulant_trace(column: tuple[float, ...], power: int = 7) -> float:
    """Take a nonnegative power's trace for a nonempty real circulant column."""
    indices = np.arange(len(column))
    matrix = np.asarray(column)[(indices[:, None] - indices) % len(column)]
    return float(np.trace(np.linalg.matrix_power(matrix, power)))


@circulant_trace.add(default=True)
def trace_fft(column: tuple[float, ...], power: int = 7) -> float:
    """Use the Fourier eigenvalues to compute the trace without a matrix."""
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


def test_measure_error() -> None:
    """Score every returned trace by its error against an independent answer."""
    errors = circulant_trace.measure(
        lambda trace: abs(trace - 0.75**4), (0.25, 0.25, 0.25), 4
    )
    assert max(errors.values()) < 1e-10


@circulant_trace.pytest_parametrize()
@pytest.mark.parametrize("size", [64, 256, 512])
@pytest.mark.benchmark(group="circulant_trace")
def test_benchmark(benchmark, implementation, size: int) -> None:
    """Time matrix construction and computation on identical inputs."""
    values = np.random.default_rng(7).uniform(-1, 1, size)
    column = tuple(float(value) for value in values / (1 + np.abs(values).sum()))
    with threadpool_limits(limits=1, user_api="blas"):
        expected = circulant_trace.reference(column, 7)
        result = benchmark(implementation, column, 7)
    assert result == pytest.approx(expected, rel=1e-10, abs=1e-10)
