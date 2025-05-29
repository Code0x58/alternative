import alternative
import cmath


@alternative.reference
def reference_implementation():
    """Reference implementation."""
    return 1


@reference_implementation.add
def alternative_implementation1():
    """Another implementation."""
    return int(True)


@reference_implementation.add
def alternative_implementation2():
    """Yet another implementation."""
    return abs(cmath.exp(1j * cmath.pi))


@reference_implementation.pytest_parametrize_pairs(n_cache=None, only_default=False)
def test_f(reference, implementation):
    """Compare the output of the reference (with caching) and each alternative implementation."""
    assert reference() == implementation()
