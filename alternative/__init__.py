from __future__ import annotations

import dataclasses
import inspect
import os
from collections.abc import Callable
from functools import WRAPPER_ASSIGNMENTS, lru_cache, wraps
from types import FrameType
from typing import (
    Final,
    Generic,
    ParamSpec,
    Protocol,
    TypeAlias,
    TypeVar,
    cast,
)

DEBUG = os.environ.get("ALTERNATIVE_DEBUG", "0").lower() in (
    "1",
    "yes",
    "y",
    "true",
    "t",
)


__all__ = [
    "AddTooLateError",
    "AlternativeError",
    "Alternatives",
    "CrossAlternativesImplementationError",
    "Implementation",
    "MultipleDefaultsError",
    "reference",
]


class _Undefined:
    """Sentinel type used when an optional decorator argument is omitted."""


class _SupportsLessThan(Protocol):
    def __lt__(self, other: object, /) -> bool: ...


_UNDEFINED_VALUE: Final = _Undefined()

P = ParamSpec("P")
Q = ParamSpec("Q")
R = TypeVar("R")
R_co = TypeVar("R_co", covariant=True)
M = TypeVar("M")
S = TypeVar("S")
F = TypeVar("F", bound=Callable[..., object])


class _TypedDescriptor(Protocol[P, R_co]):
    def __get__(
        self, instance: object | None, owner: type[object] | None = None, /
    ) -> Callable[P, R_co]: ...


_ImplementationSource: TypeAlias = _TypedDescriptor[P, R] | Callable[..., R]


class AlternativeError(Exception):
    """Base class for all alternative errors."""


class AddTooLateError(AlternativeError):
    """Cannot add implementations after the alternatives have been invoked."""


class MultipleDefaultsError(AlternativeError):
    """Cannot set the default implementation more than once."""


class CrossAlternativesImplementationError(AlternativeError):
    """Cannot add an Implementation object that belongs to a different Alternatives set."""


def _frame_back(frame: FrameType | None) -> FrameType | None:
    """Return the previous frame when frame inspection is available."""
    if frame is None:
        return None
    return frame.f_back


def _get_caller_path() -> str | None:
    """
    Return 'module.QualName (file.py:line)' pointing to the line
    that invoked the caller of this function.
    Falls back to '<unknown module>.<unknown> (<unknown location>)'
    if there is no two-up Python frame (e.g. called directly from C embedding).
    """
    frame = inspect.currentframe()
    # Walk back two frames: 0=this, 1=caller, 2=caller of caller
    caller = _frame_back(_frame_back(frame))

    # Walk through frames in this file, since they are not useful call sites.
    while caller is not None and caller.f_code.co_filename == __file__:
        caller = _frame_back(caller)
    if caller is None:
        return "<unknown module>.<unknown> (<unknown location>)"
    code = caller.f_code
    module = caller.f_globals.get("__name__", "<unknown module>")
    qualname = getattr(code, "co_qualname", code.co_name)

    filename = code.co_filename or "<unknown file>"
    lineno = caller.f_lineno or "?"
    location = f"{filename}:{lineno}"

    return f"{module}.{qualname} ({location})"


def _maybe_get_caller_path() -> str | None:
    """Return the call site if DEBUG is True, otherwise None."""
    if DEBUG:
        return _get_caller_path()
    return None


def _bind_implementation(
    implementation: _ImplementationSource[P, R],
    instance: object | None,
    owner: type[object] | None,
) -> Callable[..., R]:
    """Bind an implementation using descriptor semantics when available."""
    if owner is None and instance is not None:
        owner = type(instance)

    if hasattr(implementation, "__get__") and owner is not None:
        return cast(_TypedDescriptor[P, R], implementation).__get__(instance, owner)
    return cast(Callable[..., R], implementation)


def _bind_test_implementation(
    implementation: _ImplementationSource[P, R],
    instance: object | None,
    owner: type[object] | None,
) -> Callable[..., R]:
    """Bind test parameters, or unwrap descriptors that need an explicit receiver."""
    if owner is None:
        descriptor = (
            implementation.implementation
            if isinstance(implementation, Implementation)
            else implementation
        )
        if isinstance(descriptor, (classmethod, staticmethod)):
            return cast(Callable[..., R], descriptor.__func__)
    return _bind_implementation(implementation, instance, owner)


class _CallableMetadata:
    """Resolve annotations lazily on the original callable across Python versions."""

    def __getattribute__(self, name: str) -> object:
        if name == "__annotations__":
            source = object.__getattribute__(self, "__wrapped__")
            return getattr(source, name, {})
        return object.__getattribute__(self, name)


def _set_wrapper_metadata(
    wrapper: object, implementation: _ImplementationSource[P, R]
) -> None:
    """Preserve inspectable metadata without copying implementation attributes."""
    source = (
        implementation.__func__
        if isinstance(implementation, (classmethod, staticmethod))
        else implementation
    )
    for name in (*WRAPPER_ASSIGNMENTS, "__annotations__"):
        if name == "__annotations__":
            continue
        try:
            value = getattr(source, name)
        except AttributeError:
            continue
        object.__setattr__(wrapper, name, value)
    object.__setattr__(wrapper, "__wrapped__", source)


@dataclasses.dataclass(frozen=True)
class _BoundAlternatives(_CallableMetadata, Generic[S, P, R, Q]):
    alternatives: Alternatives[S, P, R, Q]
    instance: object | None
    owner: type[object] | None

    def __post_init__(self) -> None:
        """Expose the reference's signature with this receiver already bound."""
        _set_wrapper_metadata(
            self,
            _bind_implementation(
                self.alternatives.reference.implementation, self.instance, self.owner
            ),
        )

    def __call__(self, /, *args: object, **kwargs: object) -> R:
        implementation: Callable[..., R] = _bind_implementation(
            self.alternatives.callable, self.instance, self.owner
        )
        return implementation(*args, **kwargs)

    def add(
        self,
        implementation: object = _UNDEFINED_VALUE,
        *,
        default: bool = False,
    ) -> object:
        add = cast(Callable[..., object], self.alternatives.add)
        return add(implementation, default=default)

    @property
    def implementations(self) -> tuple[Implementation[S, P, R, Q], ...]:
        return self.alternatives.implementations

    @property
    def reference(self) -> Implementation[S, P, R, Q]:
        return self.alternatives.reference

    @property
    def callable(self) -> _ImplementationSource[P, R]:
        return self.alternatives.callable

    def pytest_parametrize(
        self,
        test: F | _Undefined = _UNDEFINED_VALUE,
        *,
        only_default: bool = False,
    ) -> F | Callable[[F], F]:
        """Parametrize tests with implementations bound to this receiver."""
        # Dataclass instance fields store descriptors without invoking __get__.
        return cast(Alternatives[S, P, R, Q], self.alternatives)._pytest_parametrize(
            test,
            only_default=only_default,
            instance=self.instance,
            owner=self.owner,
        )

    def pytest_parametrize_pairs(
        self,
        test: F | _Undefined = _UNDEFINED_VALUE,
        *,
        n_cache: int | None = 0,
        double_reference: bool = False,
        only_default: bool = False,
    ) -> F | Callable[[F], F]:
        """Compare implementations bound to this receiver with a cached reference."""
        return cast(
            Alternatives[S, P, R, Q], self.alternatives
        )._pytest_parametrize_pairs(
            test,
            n_cache=n_cache,
            double_reference=double_reference,
            only_default=only_default,
            instance=self.instance,
            owner=self.owner,
        )


@dataclasses.dataclass(frozen=True)
class _BoundImplementation(_CallableMetadata, Generic[S, P, R, Q]):
    implementation: Implementation[S, P, R, Q]
    instance: object | None
    owner: type[object] | None

    def __post_init__(self) -> None:
        """Expose this implementation's bound signature and documentation."""
        _set_wrapper_metadata(
            self,
            _bind_implementation(
                self.implementation.implementation, self.instance, self.owner
            ),
        )

    def __call__(self, /, *args: object, **kwargs: object) -> R:
        implementation: Callable[..., R] = _bind_implementation(
            self.implementation.implementation, self.instance, self.owner
        )
        return implementation(*args, **kwargs)

    @property
    def alternatives(self) -> Alternatives[S, P, R, Q]:
        return cast(Alternatives[S, P, R, Q], self.implementation.alternatives)

    def add(
        self,
        implementation: object = _UNDEFINED_VALUE,
        *,
        default: bool = False,
    ) -> object:
        add = cast(Callable[..., object], self.implementation.add)
        return add(implementation, default=default)


class Alternatives(_CallableMetadata, Generic[S, P, R, Q]):
    def __init__(
        self,
        implementation: _ImplementationSource[P, R],
        *,
        default: bool = False,
    ):
        _set_wrapper_metadata(self, implementation)
        imp = Implementation(self, implementation, label=_maybe_get_caller_path())
        self._reference = imp
        # tracks the active implementation
        self._default: Implementation[S, P, R, Q] | None = None
        self._debug_default: str | None = None

        self._callable: _ImplementationSource[P, R] | None = None

        # beware the order of this depends on the sequence of imports, so may vary between entrypoints
        self._implementations: list[Implementation[S, P, R, Q]] = []
        self._implementations_used: bool = False
        """indicates if the list of implementations has been used though the external API"""
        self._debug_implementations_used: str | None = None
        self.add(imp, default=default)

    def add(
        self,
        implementation: object = _UNDEFINED_VALUE,
        *,
        default: bool = False,
    ) -> object:
        if self._implementations_used:
            # avoid surprises from implementation changes after selection/inspection
            if DEBUG:
                msg = f"added implementation after first invocation at {self._debug_implementations_used}"
            else:
                msg = None
            raise AddTooLateError(msg)

        if isinstance(implementation, _Undefined):

            def wrapper(
                implementation: _ImplementationSource[P, R],
            ) -> Implementation[S, P, R, Q]:
                add = cast(Callable[..., Implementation[S, P, R, Q]], self.add)
                return add(implementation, default=default)

            return wrapper

        label = _maybe_get_caller_path()
        if isinstance(implementation, Alternatives):
            source = cast(Alternatives[S, P, R, Q], implementation)
            implementation = source.reference.implementation
        if (
            isinstance(self.reference.implementation, staticmethod)
            and callable(implementation)
            and not isinstance(implementation, (Implementation, staticmethod))
        ):
            # Imported functions retain the reference's static binding contract.
            implementation = staticmethod(implementation)
        if not isinstance(implementation, Implementation):
            imp = Implementation(
                self,
                cast(_ImplementationSource[P, R], implementation),
                label=label,
            )
        elif implementation.alternatives is not self:
            raise CrossAlternativesImplementationError(
                f"Cannot add {implementation!r} to {self.reference!r}; "
                "it belongs to a different Alternatives set. "
                "Pass implementation.implementation to clone explicitly."
            )
        else:
            imp = Implementation(self, implementation.implementation, label=label)

        if default:
            if self._default is not None:
                # only allow explicitly setting the default implementation once
                if DEBUG:
                    msg = f"first default was specified at {self._debug_default}; existing default={self._default!r}"
                else:
                    msg = None
                raise MultipleDefaultsError(msg)
            # there is the AddTooLate guard above which stops setting of a default after invocation - see test_default_after_invocation
            self._default = imp
            self._debug_default = _maybe_get_caller_path()

        self._implementations.append(imp)
        return imp

    @property
    def reference(self) -> Implementation[S, P, R, Q]:
        """Return the immutable reference implementation."""
        return self._reference

    @property
    def callable(self) -> _ImplementationSource[P, R]:
        """Return the active implementation.

        Setting the default implementation is disabled after this is accessed."""
        callable_ = self._callable
        if callable_ is None:
            # finalise the callable
            if self._default:
                callable_ = self._default.implementation
            else:
                callable_ = self.reference
            self._callable = callable_
            # access the list of implementations to freeze them
            implementations = self.implementations
            assert implementations
        return callable_

    @property
    def implementations(self) -> tuple[Implementation[S, P, R, Q], ...]:
        """Return an immutable snapshot and prevent further registration."""
        if not self._implementations_used:
            self._implementations_used = True
            self._debug_implementations_used = _maybe_get_caller_path()
        return tuple(self._implementations)

    def __call__(self, /, *args: object, **kwargs: object) -> R:
        implementation: Callable[..., R] = _bind_implementation(
            self.callable, None, None
        )
        return implementation(*args, **kwargs)

    def __get__(
        self, instance: object | None, owner: type[object] | None = None
    ) -> Alternatives[S, P, R, Q] | _BoundAlternatives[S, P, R, Q]:
        if instance is None and not self._binds_on_class_access():
            return self
        return _BoundAlternatives(self, instance, owner)

    def _binds_on_class_access(self) -> bool:
        """Return True when class access needs descriptor binding before calling."""
        implementation = (
            self._default.implementation
            if self._default is not None
            else self.reference.implementation
        )
        return isinstance(implementation, classmethod)

    def measure(
        self,
        /,
        operator: Callable[[R], M],
        *args: object,
        **kwargs: object,
    ) -> dict[Implementation[S, P, R, Q], M]:
        """Invoke each implementation with the given parameters, then evaluate their results with the operator.

        This is useful when comparing implementations that have different results, which can be compared by some cost.
        For example, this can be used to compare the complexity of quantum circuits that implement the same function.

        The results are sorted by the operator's result if the result is sortable (i.e. does not raise TypeError when
        __lt__(a,b) is called); otherwise they are returned in the order of the implementations.
        """
        result = {
            i: operator(cast(Callable[..., R], i)(*args, **kwargs))
            for i in self.implementations
        }
        try:
            # try to sort the dictionary by the measurements
            return dict(
                sorted(
                    result.items(),
                    key=lambda item: cast(_SupportsLessThan, item[1]),
                )
            )
        except TypeError:
            return result

    def pytest_parametrize(
        self,
        test: F | _Undefined = _UNDEFINED_VALUE,
        *,
        only_default: bool = False,
    ) -> F | Callable[[F], F]:
        """Decorator to parametrise a test function with implementations - always includes the reference implementation.

        :param test: Test function to wrap - this is elided if using the decorator syntax.
        :parameter only_default: Only include the reference and default implementations. If False, include all implementations.
        """
        return self._pytest_parametrize(
            test, only_default=only_default, instance=None, owner=None
        )

    def _pytest_parametrize(
        self,
        test: F | _Undefined,
        *,
        only_default: bool,
        instance: object | None,
        owner: type[object] | None,
    ) -> F | Callable[[F], F]:
        """Build parametrization while retaining descriptor binding context."""
        import pytest

        if isinstance(test, _Undefined):

            def decorator(f: F) -> F:
                return cast(
                    F,
                    self._pytest_parametrize(
                        f, only_default=only_default, instance=instance, owner=owner
                    ),
                )

            return decorator

        implementations = [
            _bind_test_implementation(implementation, instance, owner)
            for implementation in self._select_parametrize_implementations(
                only_default=only_default
            )
        ]

        @pytest.mark.parametrize("implementation", implementations)
        @wraps(test)
        def inner(*args: object, **kwargs: object) -> object:
            return test(*args, **kwargs)

        return cast(F, inner)

    def pytest_parametrize_pairs(
        self,
        test: F | _Undefined = _UNDEFINED_VALUE,
        *,
        n_cache: int | None = 0,
        double_reference: bool = False,
        only_default: bool = False,
    ) -> F | Callable[[F], F]:
        """Decorator to parametrise a test function with the reference and alternative implementations.

        :parameter test: Inner pytest function to parameterise with reference and alternative implementations - this is elided if using the decorator syntax.
        :parameter n_cache: Passed to lru_cache which wraps the reference implementation. Set to non-0 values for
            it to actually cache.
        :parameter double_reference: If True, the reference implementation will be included in the implementations. This
            can be used for sanity-checking equivalence tests.
        :parameter only_default: If True, only the default implementation will be used as the other implementation. If
            double_reference is True, the reference implementation will be included as well.
        """
        return self._pytest_parametrize_pairs(
            test,
            n_cache=n_cache,
            double_reference=double_reference,
            only_default=only_default,
            instance=None,
            owner=None,
        )

    def _pytest_parametrize_pairs(
        self,
        test: F | _Undefined,
        *,
        n_cache: int | None,
        double_reference: bool,
        only_default: bool,
        instance: object | None,
        owner: type[object] | None,
    ) -> F | Callable[[F], F]:
        """Build pairwise parametrization with a callable, correctly bound reference."""
        import pytest

        if isinstance(test, _Undefined):

            def decorator(f: F) -> F:
                return cast(
                    F,
                    self._pytest_parametrize_pairs(
                        f,
                        n_cache=n_cache,
                        double_reference=double_reference,
                        only_default=only_default,
                        instance=instance,
                        owner=owner,
                    ),
                )

            return decorator

        reference_implementation = cast(
            Callable[..., R],
            lru_cache(maxsize=n_cache)(
                _bind_test_implementation(
                    self.reference.implementation, instance, owner
                )
            ),
        )

        implementations = [
            _bind_test_implementation(implementation, instance, owner)
            for implementation in self._select_parametrize_pairs(
                reference_implementation=reference_implementation,
                only_default=only_default,
                double_reference=double_reference,
            )
        ]

        @pytest.mark.parametrize("reference", [reference_implementation])
        @pytest.mark.parametrize("implementation", implementations)
        @wraps(test)
        def inner(*args: object, **kwargs: object) -> object:
            return test(*args, **kwargs)

        return cast(F, inner)

    def _select_parametrize_implementations(
        self, *, only_default: bool
    ) -> list[_ImplementationSource[P, R]]:
        """Return implementation callables used for ``pytest_parametrize``."""
        if only_default:
            reference_implementation = self.reference.implementation
            default_implementation = self.callable
            implementations: list[_ImplementationSource[P, R]] = [
                reference_implementation
            ]
            if default_implementation is not reference_implementation:
                implementations.append(default_implementation)
            return implementations
        return [i.implementation for i in self.implementations]

    def _select_parametrize_pairs(
        self,
        *,
        reference_implementation: Callable[..., R],
        only_default: bool,
        double_reference: bool,
    ) -> list[_ImplementationSource[P, R]]:
        """Return implementation callables used for ``pytest_parametrize_pairs``."""
        # use underlying functions so pytest can generate readable IDs.
        implementations: list[_ImplementationSource[P, R]]
        if only_default:
            implementations = [self.callable]
            if double_reference and self.callable is not self.reference.implementation:
                implementations[:0] = [reference_implementation]
            return implementations

        implementations = [i.implementation for i in self.implementations[1:]]
        if double_reference:
            implementations[:0] = [reference_implementation]
        return implementations


@dataclasses.dataclass(frozen=True)
class Implementation(_CallableMetadata, Generic[S, P, R, Q]):
    alternatives: Alternatives[S, P, R, Q]
    implementation: _ImplementationSource[P, R]
    label: str | None = None

    def __post_init__(self):
        _set_wrapper_metadata(self, self.implementation)
        if self.label is None:
            object.__setattr__(self, "label", _maybe_get_caller_path())

    def __repr__(self) -> str:
        implementation_name = getattr(
            self.implementation, "__qualname__", repr(self.implementation)
        )
        if self.label:
            return f"Implementation({implementation_name}, label={self.label!r})"
        return f"Implementation({implementation_name})"

    def __call__(self, /, *args: object, **kwargs: object) -> R:
        implementation: Callable[..., R] = _bind_implementation(
            self.implementation, None, None
        )
        return implementation(*args, **kwargs)

    def __get__(
        self, instance: object | None, owner: type[object] | None = None
    ) -> Implementation[S, P, R, Q] | _BoundImplementation[S, P, R, Q]:
        if instance is None and not isinstance(self.implementation, classmethod):
            return self
        return _BoundImplementation(self, instance, owner)

    def add(
        self,
        implementation: object = _UNDEFINED_VALUE,
        *,
        default: bool = False,
    ) -> object:
        """Add an alternative implementation."""
        if isinstance(implementation, _Undefined):
            return self.alternatives.add(default=default)
        add = cast(Callable[..., object], self.alternatives.add)
        return add(implementation, default=default)


def reference(
    implementation: object = _UNDEFINED_VALUE,
    *,
    default: bool = False,
) -> object:
    if isinstance(implementation, _Undefined):

        def inner(f: object) -> object:
            """Add the reference implementation to the alternatives"""
            return Alternatives(
                cast(_ImplementationSource[..., object], f),
                default=default,
            )

        return inner
    else:
        return Alternatives(
            cast(_ImplementationSource[..., object], implementation),
            default=default,
        )
