"""Execute the tutorial's correctness, equivalence, and timing examples."""

import pytest

from . import total

CASES = [
    ((), 0),
    ((1,), 1),
    ((1, -2, 3), 2),
    ((2, 2, 2), 6),
    ((2**100, 1, -(2**100)), 1),
]


@total.pytest_parametrize()
@pytest.mark.parametrize(("values", "expected"), CASES)
def test_expected_totals(
    implementation, values: tuple[int, ...], expected: int
) -> None:
    """Every implementation satisfies independent expected results."""
    assert implementation(values) == expected


@total.pytest_parametrize_pairs()
@pytest.mark.parametrize(("values", "expected"), CASES)
def test_equivalent_totals(
    reference, implementation, values: tuple[int, ...], expected: int
) -> None:
    """Each candidate matches the reference on the same reusable inputs."""
    assert reference(values) == implementation(values) == expected


@total.pytest_parametrize()
def test_algorithm_benchmark(benchmark, implementation) -> None:
    """Time underlying algorithms without the production dispatch wrapper."""
    values = tuple(range(1_000))
    assert benchmark(implementation, values) == 499_500


def test_production_benchmark(benchmark) -> None:
    """Include default dispatch when measuring the production entry point."""
    values = tuple(range(1_000))
    assert benchmark(total, values) == 499_500
