import operator

import alternative


@alternative.reference
def make_four():
    """Reference implementation."""
    return "1 + 1 + 1 + 1"


@make_four.add
def make_four_factor():
    """Another implementation."""
    return "2 * 2"


@make_four.add
def make_four_literal():
    """Another implementation."""
    return "4"


@make_four.pytest_parametrize_pairs()
def test_f(reference, implementation):
    """Compare the output of the reference (with caching) and each alternative implementation."""
    assert eval(reference()) == eval(implementation())


def test_measure():
    """The measure is applied to all the results"""
    measurements = make_four.measure(len)
    assert [(i.implementation.__name__, m) for i, m in measurements.items()] == list(
        {"make_four_literal": 1, "make_four_factor": 5, "make_four": 13}.items()
    )


def test_measure_unsortable():
    """The measure is applied to all the results"""
    # convert the length to a complex number to make it unsortable
    measurements = make_four.measure(lambda code: len(code) + 0j)
    # the measurements are in the order of the implementations
    assert [(i.implementation.__name__, m) for i, m in measurements.items()] == list(
        {"make_four": 13, "make_four_factor": 5, "make_four_literal": 1}.items()
    )
