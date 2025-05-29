import re
from unittest.mock import MagicMock

import pytest

import alternative
from inspect import signature


def imp_for_cmp(imp: alternative.Implementation | None) -> dict | None:
    if imp is None:
        return None
    return {"i": imp.implementation}


def test_add_happy_path():
    """An implementation can be added though an existing implementation, on top of the reference implementation."""

    @alternative.reference
    def f():
        return 1

    # this uses Alternatives.add
    @f.add
    def alt2():
        return 2

    # this uses Implementation.add
    @alt2.add(default=True)
    def alt3():
        return 3

    # the default implementation for this meta-function is alt3, so we get the result from that
    assert f() == 3
    # as these two are alternative implementations, invoking them does not try using other alternatives
    assert alt2() == 2
    assert alt3() == 3


def test_coupled_signatures():
    """The signatures of reference, Alternative.add, and Implementation.add are aligned."""
    ref_sig = signature(alternative.reference)  # pyrefly: ignore
    alt_sig = signature(alternative.Alternatives.add)  # pyrefly: ignore
    imp_sig = signature(alternative.Implementation.add)  # pyrefly: ignore
    assert alt_sig.parameters == imp_sig.parameters
    # skip the self-parameter to give matching signatures
    assert (
        alt_sig.replace(
            parameters=tuple(list(alt_sig.parameters.values())[1:])
        ).parameters
        == ref_sig.parameters
    )


@pytest.mark.parametrize(
    "kwargs",
    [
        {"default": True},
        {"default": False},
        {},
    ],
)
def test_register_approaches_equivalent(monkeypatch, kwargs: dict):
    """Registering has expected implicit attributes on the alternatives."""

    def f():
        return 1

    mock = MagicMock(spec=alternative.Alternatives)
    monkeypatch.setattr(alternative, "Alternatives", mock)
    f_indirect: alternative.Alternatives = alternative.reference()(f)
    assert mock.call_count == 1
    f_direct = alternative.reference(f)
    assert mock.call_count == 2

    assert f_indirect == f_direct
    assert mock.call_args_list[0] == mock.call_args_list[1]


def test_implicit_reference_implementation():
    """The reference implementation is used if no explicit default is specified."""

    @alternative.reference(default=False)
    def a():
        return 1

    @a.add(default=False)
    def alt2():
        return 2

    # the reference implementation is the default unless one is specified
    # explicitly defaulting stops subsequent override
    assert a() == 1


def test_explicit_default_implementation():
    """The default implementation is used if specified."""

    @alternative.reference(default=False)
    def a():
        return 1

    @a.add(default=True)
    def alt2():
        return 2

    assert a() == 2


def test_multiple_defaults(debug_func: str | None, monkeypatch):
    """The default can only be set once."""

    # the reference was chosen as the default implementation
    @alternative.reference
    def b():
        return 1

    # this will be an Implementation object instead of the original Alternatives, so has extra indirection
    @b.add(default=True)
    def alt1():
        return 2

    def alt2():
        return 3

    # default cannot be specified multiple times
    if debug_func:
        match = rf"^first default was specified at test_alternative\.{debug_func} \({re.escape(__file__)}:\d+\)"
    else:
        match = "^None$"
    with pytest.raises(alternative.MultipleDefaults, match=match):
        alt1.add(alt2, default=True)
    # but an additional implementation can be registered
    alt1.add(alt2, default=False)
    alt1.add(alt2)
    assert b() == 2


def test_default_after_invocation(debug_func: str | None):
    """The default cannot be set after an invocation."""

    # the reference was chosen as the default implementation
    @alternative.reference
    def f():
        return 1

    def alt():
        return 2

    # default cannot be specified multiple times
    if debug_func:
        match = rf"^added implementation after first invocation at test_alternative\.{debug_func} \({re.escape(__file__)}:\d+\)"
    else:
        match = "^None$"

    assert f() == 1
    with pytest.raises(alternative.AddTooLate, match=match):
        f.add(alt, default=True)


@pytest.fixture(params=[True, False], ids=["debug", "no-debug"])
def debug_func(request: pytest.FixtureRequest, monkeypatch) -> str | None:
    """Configure the debug flag if needed and return the name of the test function if debugging."""
    if not request.param:
        assert not alternative.DEBUG
        return None

    monkeypatch.setattr(alternative, "DEBUG", True)
    return request.node.originalname


def test_no_add_after_invoke(debug_func: str | None):
    """Alternatives may not be added after an invocation."""

    @alternative.reference
    def f():
        return 1

    # adding alternatives works until there has been an invocation
    @f.add
    def alt():
        return 2

    f()

    if debug_func:
        match = rf"^added implementation after first invocation at test_alternative\.{debug_func} \({re.escape(__file__)}:\d+\)"
    else:
        match = "^None$"
    with pytest.raises(alternative.AddTooLate, match=match):

        @f.add
        def alt():
            return 3

    # you can still get the list of implementations
    assert len(f.implementations) == 2


def test_no_additions_after_implementations_access(debug_func: str | None = None):
    """Alternatives may not be added after the reference or default implementations are accessed."""

    @alternative.reference
    def f():
        return 1

    # this access will freeze the implementations to avoid surprises down the line
    assert len(f.implementations) == 1

    if debug_func:
        match = rf"^added implementation after first invocation at test_alternative\.{debug_func} \({re.escape(__file__)}:\d+\)$"
    else:
        match = "^None$"

    with pytest.raises(alternative.AddTooLate, match=match):

        @f.add
        def alt():
            return 2


def test_add_from_other_alternatives():
    """Implementations from one alternative set can be added as an alternative to another alternative set.

    The new implementation is a copy of the original implementation, with the target alternative set as its alternatives.
    """

    @alternative.reference
    def f1():
        return 1

    @f1.add
    def alt1():
        return 2

    @alternative.reference
    def f2():
        return 10

    # f1 comes from a different set of alternatives of f2
    assert isinstance(f1, alternative.Alternatives)
    assert f2.add(f1).alternatives is f2

    # alt1 comes from a different set of alternatives of f2
    assert isinstance(alt1, alternative.Implementation)
    assert f2.add(alt1).alternatives is f2

    # when duplicating an implementation, a new Implementation object is returned
    assert f1.add(alt1) is not alt1
