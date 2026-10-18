"""Verify signatures and documentation survive registration and binding."""

import inspect
import sys
from functools import partial

import pytest

import alternative


def test_function_metadata_preserves_reference_contract() -> None:
    """Reference metadata stays stable when a different candidate is selected."""

    def original(value: int = 2, *, scale: int = 3) -> int:
        """Multiply by a configurable scale."""
        return value * scale

    wrapped = alternative.reference(original)

    @wrapped.add(default=True)
    def candidate(value: int = 2, *, scale: int = 3, extra: int = 0) -> int:
        """Offer a broader candidate signature."""
        return value * scale + extra

    for target in (wrapped, wrapped.reference):
        assert inspect.signature(target) == inspect.signature(original)
        assert inspect.unwrap(target) is original
        assert target.__doc__ == original.__doc__
        assert target.__name__ == original.__name__
        assert target.__qualname__ == original.__qualname__
        assert target.__module__ == original.__module__
        assert target.__annotations__ == original.__annotations__
    assert "extra" in inspect.signature(candidate).parameters
    assert candidate.__doc__ == "Offer a broader candidate signature."
    wrapped.add(original)


@pytest.mark.parametrize("method_name", ["instance", "factory", "static"])
def test_bound_metadata_preserves_receiver_signatures(method_name: str) -> None:
    """Inspecting class, instance, and candidate views does not freeze registration."""

    class Example:
        """Supply the three supported descriptor styles."""

        @alternative.reference
        def instance(self, value: int = 2, *, scale: int = 3) -> int:
            """Multiply through an instance."""
            return value * scale

        @alternative.reference
        @classmethod
        def factory(cls, value: int = 2, *, scale: int = 3) -> int:
            """Multiply through a class."""
            return value * scale

        @alternative.reference
        @staticmethod
        def static(value: int = 2, *, scale: int = 3) -> int:
            """Multiply without a receiver."""
            return value * scale

    descriptor = Example.__dict__[method_name]
    raw = inspect.unwrap(descriptor)
    candidate = descriptor.add(descriptor.reference.implementation)
    owner = type("Child", (Example,), {"candidate": candidate})
    for receiver in (owner, owner()):
        target = getattr(receiver, method_name)
        candidate_name = "candidate"
        direct = getattr(receiver, candidate_name)
        expected = raw.__get__(None if receiver is owner else receiver, owner)
        if method_name == "factory":
            expected = raw.__get__(owner, type(owner))
        elif method_name == "static":
            expected = raw
        assert inspect.signature(target) == inspect.signature(expected)
        assert inspect.signature(direct) == inspect.signature(expected)
        assert target.__doc__ == direct.__doc__ == raw.__doc__
        assert inspect.get_annotations(target) == inspect.get_annotations(raw)
        assert inspect.get_annotations(direct) == inspect.get_annotations(raw)
    descriptor.add(descriptor.reference.implementation)


@pytest.mark.parametrize("source", [len, partial(int, base=10)])
def test_incomplete_callable_metadata_does_not_prevent_registration(source) -> None:
    """Builtins and partials need not expose every standard function attribute."""
    wrapped = alternative.reference(source)
    assert inspect.unwrap(wrapped) is source
    assert wrapped.__doc__ == source.__doc__
    assert wrapped.__annotations__ == {}


def test_missing_optional_metadata_remains_missing() -> None:
    """Callables without names still raise AttributeError when a name is requested."""
    wrapped = alternative.reference(partial(int, base=10))
    with pytest.raises(AttributeError):
        _ = wrapped.__name__


@pytest.mark.parametrize(
    "wrapper", [alternative.Alternatives, alternative.Implementation]
)
def test_wrapper_classes_keep_constructor_signatures(wrapper) -> None:
    """Instance unwrap metadata must not masquerade as a class's wrapped callable."""
    assert "implementation" in inspect.signature(wrapper).parameters
    with pytest.raises(AttributeError):
        _ = wrapper.__wrapped__


def test_metadata_does_not_copy_implementation_state() -> None:
    """Function attributes cannot overwrite a wrapper's registration helpers."""

    def original() -> int:
        """Return a constant."""
        return 1

    original.__dict__["add"] = "unrelated function attribute"
    wrapped = alternative.reference(original)
    wrapped.add(lambda: 1)


@pytest.mark.skipif(sys.version_info < (3, 14), reason="Requires deferred annotations")
def test_deferred_annotations_are_not_evaluated_during_registration() -> None:
    """A class can refer to itself before its decorator has finished executing."""

    class Example:
        """Refer to this class in an unevaluated return annotation."""

        @alternative.reference
        def method(self) -> Example:  # noqa: F821 - evaluated lazily on Python 3.14+
            """Return this instance."""
            return self

    assert inspect.get_annotations(Example().method)["return"] is Example
