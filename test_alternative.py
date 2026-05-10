import re
from inspect import signature
from typing import Callable, cast
from unittest.mock import MagicMock

import pytest

import alternative


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
    ref_sig = signature(cast(Callable[..., object], alternative.reference))
    alt_sig = signature(cast(Callable[..., object], alternative.Alternatives.add))
    imp_sig = signature(cast(Callable[..., object], alternative.Implementation.add))
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
    with pytest.raises(alternative.MultipleDefaultsError, match=match):
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
    with pytest.raises(alternative.AddTooLateError, match=match):
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
    with pytest.raises(alternative.AddTooLateError, match=match):

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

    with pytest.raises(alternative.AddTooLateError, match=match):

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
    with pytest.raises(alternative.CrossAlternativesImplementationError):
        f2.add(alt1)

    # adding an implementation to its own alternatives clones the wrapper
    assert f1.add(alt1) is not alt1


def test_measure_sorts_sortable_measurements() -> None:
    """Measurements are sorted by the measured value when the values are sortable."""

    @alternative.reference
    def make_four() -> str:
        return "1 + 1 + 1 + 1"

    @make_four.add
    def make_four_factor() -> str:
        return "2 * 2"

    @make_four.add
    def make_four_literal() -> str:
        return "4"

    measurements = make_four.measure(len)

    assert list(measurements.items()) == [
        (make_four_literal, 1),
        (make_four_factor, 5),
        (make_four.reference, 13),
    ]


def test_measure_preserves_registration_order_for_unsortable_measurements() -> None:
    """Measurements keep registration order when the measured values cannot be sorted."""

    @alternative.reference
    def make_four() -> str:
        return "1 + 1 + 1 + 1"

    @make_four.add
    def make_four_factor() -> str:
        return "2 * 2"

    @make_four.add
    def make_four_literal() -> str:
        return "4"

    measurements = make_four.measure(lambda code: len(code) + 0j)

    assert list(measurements.items()) == [
        (make_four.reference, 13 + 0j),
        (make_four_factor, 5 + 0j),
        (make_four_literal, 1 + 0j),
    ]


def test_cross_owner_add_error():
    """Adding a cross-owner implementation raises a dedicated explicit error."""

    @alternative.reference
    def source():
        return 1

    @source.add
    def source_alt():
        return 2

    @alternative.reference
    def target():
        return 3

    expected = (
        r"^Cannot add "
        r"Implementation\(test_cross_owner_add_error\.<locals>\.source_alt(?:, label='[^']+')?\) "
        r"to Implementation\(test_cross_owner_add_error\.<locals>\.target(?:, label='[^']+')?\); "
        r"it belongs to a different Alternatives set\. "
        r"Pass implementation\.implementation to clone explicitly\.$"
    )
    with pytest.raises(
        alternative.CrossAlternativesImplementationError, match=expected
    ):
        target.add(source_alt)


def test_implementation_label_populated_in_debug(monkeypatch):
    """Implementation labels include caller metadata in debug mode."""
    monkeypatch.setattr(alternative, "DEBUG", True)

    @alternative.reference
    def f():
        return 1

    @f.add
    def alt():
        return 2

    expected_prefix = (
        f"test_alternative.test_implementation_label_populated_in_debug ({__file__}"
    )

    f_reference_prefix, _, f_reference_line = f.reference.label.rpartition(":")
    assert f_reference_prefix == expected_prefix
    assert f_reference_line[:-1].isdigit()

    alt_prefix, _, alt_line = alt.label.rpartition(":")
    assert alt_prefix == expected_prefix
    assert alt_line[:-1].isdigit()

    assert (
        repr(alt)
        == f"Implementation(test_implementation_label_populated_in_debug.<locals>.alt, label={alt.label!r})"
    )


def test_implementation_label_safe_when_caller_unavailable(monkeypatch):
    """Implementation label uses fallback when caller information cannot be resolved."""
    monkeypatch.setattr(alternative, "DEBUG", True)
    monkeypatch.setattr(
        alternative,
        "_get_caller_path",
        lambda: "<unknown module>.<unknown> (<unknown location>)",
    )

    @alternative.reference
    def f():
        return 1

    assert f.reference.label == "<unknown module>.<unknown> (<unknown location>)"


def test_implementation_repr_without_label(monkeypatch):
    """Implementation repr omits label when no label metadata is available."""
    monkeypatch.setattr(alternative, "DEBUG", False)

    @alternative.reference
    def f():
        return 1

    @f.add
    def alt():
        return 2

    assert alt.label is None
    assert (
        repr(alt)
        == "Implementation(test_implementation_repr_without_label.<locals>.alt)"
    )


def test_instance_method_binding() -> None:
    """Alternatives bind instance methods through descriptor access."""

    class Calculator:
        def __init__(self, offset: int):
            self.offset = offset

        @alternative.reference
        def add(self, value: int) -> tuple[str, int]:
            return ("reference", self.offset + value)

        @add.add(default=True)
        def add_default(self, value: int) -> tuple[str, int]:
            return ("default", self.offset + value)

        @add.add
        def add_extra(self, value: int) -> tuple[str, int]:
            return ("extra", self.offset + value)

    calculator = Calculator(10)

    assert calculator.add(5) == ("default", 15)
    assert calculator.add_default(5) == ("default", 15)
    assert calculator.add_extra(5) == ("extra", 15)
    assert Calculator.add(calculator, 5) == ("default", 15)
    assert Calculator.add_extra(calculator, 5) == ("extra", 15)
    assert calculator.add_extra.alternatives is Calculator.__dict__["add"]
    descriptor = cast(
        alternative.Alternatives[Calculator, [int], tuple[str, int]],
        Calculator.__dict__["add"],
    )
    assert descriptor.__get__(calculator)(5) == ("default", 15)


def test_classmethod_binding() -> None:
    """Alternatives bind classmethod implementations to the owner class."""

    class Factory:
        marker = "Factory"

        @alternative.reference
        @classmethod
        def build(cls, value: str) -> tuple[str, str, str]:
            return ("reference", cls.marker, value)

        @build.add(default=True)
        @classmethod
        def build_default(cls, value: str) -> tuple[str, str, str]:
            return ("default", cls.marker, value)

        @build.add
        @classmethod
        def build_extra(cls, value: str) -> tuple[str, str, str]:
            return ("extra", cls.marker, value)

    class ChildFactory(Factory):
        marker = "ChildFactory"

    assert Factory.build("a") == ("default", "Factory", "a")
    assert Factory().build("a") == ("default", "Factory", "a")
    assert Factory.build_default("a") == ("default", "Factory", "a")
    assert Factory.build_extra("a") == ("extra", "Factory", "a")
    assert ChildFactory.build("a") == ("default", "ChildFactory", "a")
    assert ChildFactory.build_extra("a") == ("extra", "ChildFactory", "a")


def test_staticmethod_binding() -> None:
    """Alternatives preserve staticmethod binding from class and instance access."""

    class Parser:
        @alternative.reference
        @staticmethod
        def parse(value: str) -> tuple[str, str]:
            return ("reference", value)

        @parse.add(default=True)
        @staticmethod
        def parse_default(value: str) -> tuple[str, str]:
            return ("default", value)

        @parse.add
        @staticmethod
        def parse_extra(value: str) -> tuple[str, str]:
            return ("extra", value)

    assert Parser.parse("x") == ("default", "x")
    assert Parser().parse("x") == ("default", "x")
    assert Parser.parse_default("x") == ("default", "x")
    assert Parser.parse_extra("x") == ("extra", "x")


def test_bound_attribute_access_does_not_freeze_implementations() -> None:
    """Accessing a method alternative does not freeze registrations before invocation."""

    class Counter:
        @alternative.reference
        def value(self) -> int:
            return 1

    bound_value = Counter().value

    @Counter.value.add(default=True)
    def value_default(self) -> int:
        return 2

    assert bound_value() == 2


def test_bound_method_registration_delegates_to_alternatives() -> None:
    """Bound alternatives expose registration and metadata without dynamic attribute typing."""

    class Counter:
        @alternative.reference
        def value(self) -> int:
            return 1

    counter = Counter()

    @counter.value.add(default=True)
    def value_default(self) -> int:
        return 2

    @value_default.__get__(counter, type(counter)).add
    def value_extra(self) -> int:
        return 3

    assert counter.value.implementations == Counter.__dict__["value"].implementations
    assert counter.value.reference is Counter.__dict__["value"].reference
    assert counter.value.callable is Counter.__dict__["value"].callable
    assert counter.value() == 2
    assert value_default.__get__(counter, type(counter))() == 2
    assert value_extra(counter) == 3
