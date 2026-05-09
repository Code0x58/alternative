import inspect
from collections.abc import Callable

import alternative
import pytest


@alternative.reference
def f():
    return 1


@f.add
def alt1():
    return 1


@f.add
def alt2():
    return 1


def _parametrize_values(test_func, arg_name: str):
    """Return the parameter values configured by pytest.mark.parametrize for an argument."""
    return [
        mark.args[1]
        for mark in test_func.pytestmark
        if mark.name == "parametrize" and mark.args[0] == arg_name
    ]


@f.pytest_parametrize_pairs
def test_f(reference, implementation):
    """Default pair parametrization compares each implementation with the reference."""
    assert reference() == implementation()


@pytest.mark.parametrize("only_default", [False, True])
def test_select_parametrize_implementations(only_default: bool):
    """The selected implementation callables match the expected set for each mode."""

    @alternative.reference
    def reference_impl():
        return 1

    @reference_impl.add(default=True)
    def default_impl():
        return 2

    @reference_impl.add
    def extra_impl():
        return 3

    def parametrized(implementation: Callable[[], int]) -> None:
        """Placeholder test used to inspect pytest parametrization values."""
        assert implementation() in {1, 2, 3}

    decorated = reference_impl.pytest_parametrize(
        parametrized, only_default=only_default
    )
    selected = _parametrize_values(decorated, "implementation")[0]
    default_callable = default_impl.implementation
    extra_callable = extra_impl.implementation
    if only_default:
        assert selected == [reference_impl.reference.implementation, default_callable]
    else:
        assert selected == [
            reference_impl.reference.implementation,
            default_callable,
            extra_callable,
        ]


def test_select_parametrize_implementations_with_implicit_default():
    """Only-default parametrization includes the wrapper when the reference default is implicit."""

    @alternative.reference
    def reference_impl():
        return 1

    @reference_impl.add
    def extra_impl():
        return 2

    def parametrized(implementation: Callable[[], int]) -> None:
        """Placeholder test used to inspect pytest parametrization values."""
        assert implementation() in {1, 2}

    decorated = reference_impl.pytest_parametrize(parametrized, only_default=True)
    selected = _parametrize_values(decorated, "implementation")[0]

    assert selected == [
        reference_impl.reference.implementation,
        reference_impl.callable,
    ]


def test_select_parametrize_implementations_with_explicit_reference_default():
    """Only-default parametrization does not duplicate an explicitly defaulted reference."""

    @alternative.reference(default=True)
    def reference_impl():
        return 1

    @reference_impl.add
    def extra_impl():
        return 2

    def parametrized(implementation: Callable[[], int]) -> None:
        """Placeholder test used to inspect pytest parametrization values."""
        assert implementation() in {1, 2}

    decorated = reference_impl.pytest_parametrize(parametrized, only_default=True)
    selected = _parametrize_values(decorated, "implementation")[0]

    assert selected == [reference_impl.reference.implementation]


@pytest.mark.parametrize("only_default", [False, True])
@pytest.mark.parametrize("double_reference", [False, True])
def test_pytest_parametrize_pairs_signature_and_parameters(
    only_default: bool, double_reference: bool
):
    """Pair parametrization preserves signature and selects expected reference/implementation values."""

    @alternative.reference
    def reference_impl(x: int, y: int = 0) -> int:
        return x + y

    @reference_impl.add(default=True)
    def default_impl(x: int, y: int = 0) -> int:
        return x + y

    @reference_impl.add
    def extra_impl(x: int, y: int = 0) -> int:
        return x + y

    def pair_test(reference, implementation, x: int, y: int = 0):
        return reference(x, y) == implementation(x, y)

    decorated = reference_impl.pytest_parametrize_pairs(
        pair_test,
        only_default=only_default,
        double_reference=double_reference,
    )

    assert inspect.signature(decorated) == inspect.signature(pair_test)

    reference_values = _parametrize_values(decorated, "reference")
    implementation_values = _parametrize_values(decorated, "implementation")
    assert len(reference_values) == 1
    assert len(reference_values[0]) == 1

    implementation_names = [func.__name__ for func in implementation_values[0]]
    expected_implementations = (
        ["default_impl"] if only_default else ["default_impl", "extra_impl"]
    )
    if double_reference:
        expected_implementations = ["reference_impl", *expected_implementations]
    assert implementation_names == expected_implementations
    assert len(implementation_values[0]) == len(expected_implementations)

    reference_callable = reference_values[0][0]
    default_callable = default_impl.implementation
    extra_callable = extra_impl.implementation

    assert decorated(reference_callable, default_callable, 2, y=3)
    if "extra_impl" in expected_implementations:
        assert decorated(reference_callable, extra_callable, 2, y=3)
