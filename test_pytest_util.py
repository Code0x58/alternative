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


@f.pytest_parametrize_pairs
def test_f(reference, implementation):
    # FIXME: check the use of parameters is correct + decorator use
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

    selected = reference_impl._select_parametrize_implementations(  # pyrefly: ignore
        only_default=only_default
    )
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


@pytest.mark.parametrize(
    ("only_default", "double_reference"),
    [(False, False), (False, True), (True, False), (True, True)],
)
def test_select_parametrize_pairs(only_default: bool, double_reference: bool):
    """The selected pair callables preserve reference inclusion and exclusions."""

    @alternative.reference
    def reference_impl():
        return 1

    @reference_impl.add(default=True)
    def default_impl():
        return 2

    @reference_impl.add
    def extra_impl():
        return 3

    reference_wrapper = lambda: None  # noqa: E731
    selected = reference_impl._select_parametrize_pairs(  # pyrefly: ignore
        reference_implementation=reference_wrapper,
        only_default=only_default,
        double_reference=double_reference,
    )
    default_callable = default_impl.implementation
    extra_callable = extra_impl.implementation

    if only_default and double_reference:
        assert selected == [reference_wrapper, default_callable]
    elif only_default:
        assert selected == [default_callable]
    elif double_reference:
        assert selected == [reference_wrapper, default_callable, extra_callable]
    else:
        assert selected == [default_callable, extra_callable]
