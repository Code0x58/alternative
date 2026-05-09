import alternative


@alternative.reference
def reference_implementation():
    """Reference implementation."""
    return 1


@reference_implementation.add
def alternative_implementation1():
    """Another implementation."""
    return int(True)


@reference_implementation.pytest_parametrize(only_default=False)
def test_f(benchmark, implementation):
    """Benchmark all implementations using the pytest-benchmark `benchmark` fixture."""
    assert benchmark(implementation) == 1
