"""Benchmark real matrix work and the selected application entry point."""

from collections.abc import Iterator

import pytest
from threadpoolctl import threadpool_limits

from . import layer_trace


@pytest.fixture(scope="module", autouse=True)
def single_blas_thread() -> Iterator[None]:
    """Keep CPU allocation comparable across matrix sizes and implementations."""
    with threadpool_limits(limits=1, user_api="blas"):
        yield


def benchmark_angles(qubits: int) -> tuple[float, ...]:
    """Use deterministic, nontrivial rotations for every timed implementation."""
    return tuple((index + 1) / 10 for index in range(qubits))


@layer_trace.pytest_parametrize()
@pytest.mark.parametrize("qubits", [4, 6, 8])
@pytest.mark.benchmark(group="matrix_trace")
def test_algorithm_benchmark(benchmark, implementation, qubits: int) -> None:
    """Include construction, validation, and evaluation in each algorithm call."""
    angles = benchmark_angles(qubits)
    expected = layer_trace.reference(angles, 7)
    result = benchmark.pedantic(
        implementation, args=(angles, 7), rounds=9, iterations=10, warmup_rounds=1
    )
    assert result == pytest.approx(expected, rel=1e-10, abs=1e-10)


@pytest.mark.parametrize("qubits", [4, 6, 8])
@pytest.mark.benchmark(group="matrix_trace")
def test_production_benchmark(benchmark, qubits: int) -> None:
    """Include alternative's dispatch in the selected character implementation."""
    angles = benchmark_angles(qubits)
    expected = layer_trace.reference(angles, 7)
    result = benchmark.pedantic(
        layer_trace, args=(angles, 7), rounds=9, iterations=10, warmup_rounds=1
    )
    assert result == pytest.approx(expected, rel=1e-10, abs=1e-10)
