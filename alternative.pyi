from __future__ import annotations

from typing import (
    Callable,
    Concatenate,
    Generic,
    ParamSpec,
    Protocol,
    TypeVar,
    overload,
)

DEBUG: bool

__all__ = [
    "reference",
    "Alternatives",
    "Implementation",
    "AlternativeError",
    "AddTooLateError",
    "MultipleDefaultsError",
    "CrossAlternativesImplementationError",
]

P = ParamSpec("P")
R = TypeVar("R")
R_co = TypeVar("R_co", covariant=True)
M = TypeVar("M")
S = TypeVar("S")
_Owner = TypeVar("_Owner")
F = TypeVar("F", bound=Callable[..., object])
_A1 = TypeVar("_A1")
_A2 = TypeVar("_A2")
_A3 = TypeVar("_A3")
_A4 = TypeVar("_A4")
_A5 = TypeVar("_A5")

class _NoReceiver:
    """Marker type for descriptors that bind themselves before user calls."""

class _TypedDescriptor(Protocol[P, R_co]):
    def __get__(
        self, instance: object | None, owner: type[object] | None = None, /
    ) -> Callable[P, R_co]: ...

class _ReferenceDecorator(Protocol):
    @overload
    def __call__(
        self,
        implementation: classmethod[_Owner, P, R],
        /,
    ) -> Alternatives[_NoReceiver, P, R]: ...
    @overload
    def __call__(
        self,
        implementation: staticmethod[P, R],
        /,
    ) -> Alternatives[_NoReceiver, P, R]: ...
    @overload
    def __call__(
        self, implementation: Callable[Concatenate[type[_Owner], P], R], /
    ) -> Alternatives[_NoReceiver, P, R]: ...
    @overload
    def __call__(
        self, implementation: Callable[Concatenate[S, P], R], /
    ) -> Alternatives[S, P, R]: ...
    @overload
    def __call__(
        self, implementation: Callable[P, R], /
    ) -> Alternatives[_NoReceiver, P, R]: ...

class AlternativeError(Exception):
    """Base class for all alternative errors."""

class AddTooLateError(AlternativeError):
    """Cannot add implementations after the alternatives have been invoked."""

class MultipleDefaultsError(AlternativeError):
    """Cannot set the default implementation more than once."""

class CrossAlternativesImplementationError(AlternativeError):
    """Cannot add an Implementation object that belongs to a different Alternatives set."""

class _BoundAlternatives(Generic[S, P, R]):
    __match_args__: tuple[str, str, str]
    alternatives: Alternatives[S, P, R]
    instance: object | None
    owner: type[object] | None

    def __init__(
        self,
        alternatives: Alternatives[S, P, R],
        instance: object | None,
        owner: type[object] | None,
    ) -> None: ...
    @overload
    def __call__(self: _BoundAlternatives[S, [], R]) -> R: ...
    @overload
    def __call__(self: _BoundAlternatives[S, [_A1], R], arg1: _A1, /) -> R: ...
    @overload
    def __call__(
        self: _BoundAlternatives[S, [_A1, _A2], R], arg1: _A1, arg2: _A2, /
    ) -> R: ...
    @overload
    def __call__(
        self: _BoundAlternatives[S, [_A1, _A2, _A3], R],
        arg1: _A1,
        arg2: _A2,
        arg3: _A3,
        /,
    ) -> R: ...
    @overload
    def __call__(
        self: _BoundAlternatives[S, [_A1, _A2, _A3, _A4], R],
        arg1: _A1,
        arg2: _A2,
        arg3: _A3,
        arg4: _A4,
        /,
    ) -> R: ...
    @overload
    def __call__(
        self: _BoundAlternatives[S, [_A1, _A2, _A3, _A4, _A5], R],
        arg1: _A1,
        arg2: _A2,
        arg3: _A3,
        arg4: _A4,
        arg5: _A5,
        /,
    ) -> R: ...
    @overload
    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R: ...
    @overload
    def add(
        self: _BoundAlternatives[_NoReceiver, P, R],
        implementation: Callable[P, R]
        | Callable[Concatenate[type[_Owner], P], R]
        | classmethod[_Owner, P, R]
        | staticmethod[P, R],
        *,
        default: bool = False,
    ) -> Implementation[_NoReceiver, P, R]: ...
    @overload
    def add(
        self,
        implementation: Callable[Concatenate[S, P], R] | Implementation[S, P, R],
        *,
        default: bool = False,
    ) -> Implementation[S, P, R]: ...
    @overload
    def add(
        self, *, default: bool = False
    ) -> Callable[[Callable[..., R]], Implementation[S, P, R]]: ...
    @property
    def implementations(self) -> list[Implementation[S, P, R]]: ...
    @property
    def reference(self) -> Implementation[S, P, R]: ...
    @property
    def callable(self) -> Callable[..., R] | _TypedDescriptor[P, R]: ...

class _BoundImplementation(Generic[S, P, R]):
    __match_args__: tuple[str, str, str]
    implementation: Implementation[S, P, R]
    instance: object | None
    owner: type[object] | None

    def __init__(
        self,
        implementation: Implementation[S, P, R],
        instance: object | None,
        owner: type[object] | None,
    ) -> None: ...
    @overload
    def __call__(self: _BoundImplementation[S, [], R]) -> R: ...
    @overload
    def __call__(self: _BoundImplementation[S, [_A1], R], arg1: _A1, /) -> R: ...
    @overload
    def __call__(
        self: _BoundImplementation[S, [_A1, _A2], R], arg1: _A1, arg2: _A2, /
    ) -> R: ...
    @overload
    def __call__(
        self: _BoundImplementation[S, [_A1, _A2, _A3], R],
        arg1: _A1,
        arg2: _A2,
        arg3: _A3,
        /,
    ) -> R: ...
    @overload
    def __call__(
        self: _BoundImplementation[S, [_A1, _A2, _A3, _A4], R],
        arg1: _A1,
        arg2: _A2,
        arg3: _A3,
        arg4: _A4,
        /,
    ) -> R: ...
    @overload
    def __call__(
        self: _BoundImplementation[S, [_A1, _A2, _A3, _A4, _A5], R],
        arg1: _A1,
        arg2: _A2,
        arg3: _A3,
        arg4: _A4,
        arg5: _A5,
        /,
    ) -> R: ...
    @overload
    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R: ...
    @property
    def alternatives(self) -> Alternatives[S, P, R]: ...
    @overload
    def add(
        self: _BoundImplementation[_NoReceiver, P, R],
        implementation: Callable[P, R]
        | Callable[Concatenate[type[_Owner], P], R]
        | classmethod[_Owner, P, R]
        | staticmethod[P, R],
        *,
        default: bool = False,
    ) -> Implementation[_NoReceiver, P, R]: ...
    @overload
    def add(
        self,
        implementation: Callable[Concatenate[S, P], R] | Implementation[S, P, R],
        *,
        default: bool = False,
    ) -> Implementation[S, P, R]: ...
    @overload
    def add(
        self, *, default: bool = False
    ) -> Callable[[Callable[..., R]], Implementation[S, P, R]]: ...

class Alternatives(Generic[S, P, R]):
    reference: Implementation[S, P, R]
    _default: Implementation[S, P, R] | None
    _debug_default: str | None
    _invoked: bool
    _debug_invoked_site: str | None
    _enumerated: bool
    _callable: Callable[..., R] | _TypedDescriptor[P, R] | None
    _debug_callable_used: str | None
    _implementations: list[Implementation[S, P, R]]
    _implementations_used: bool
    _debug_implementations_used: str | None

    def __init__(
        self,
        implementation: Callable[..., R] | _TypedDescriptor[P, R],
        *,
        default: bool = False,
    ) -> None: ...
    @overload
    def add(
        self: Alternatives[_NoReceiver, P, R],
        implementation: Callable[P, R]
        | Callable[Concatenate[type[_Owner], P], R]
        | classmethod[_Owner, P, R]
        | staticmethod[P, R],
        *,
        default: bool = False,
    ) -> Implementation[_NoReceiver, P, R]: ...
    @overload
    def add(
        self,
        implementation: Callable[Concatenate[S, P], R] | Implementation[S, P, R],
        *,
        default: bool = False,
    ) -> Implementation[S, P, R]: ...
    @overload
    def add(
        self, *, default: bool = False
    ) -> Callable[[Callable[..., R]], Implementation[S, P, R]]: ...
    @property
    def callable(self) -> Callable[..., R] | _TypedDescriptor[P, R]: ...
    @property
    def implementations(self) -> list[Implementation[S, P, R]]: ...
    @overload
    def __call__(self: Alternatives[_NoReceiver, [], R]) -> R: ...
    @overload
    def __call__(self: Alternatives[_NoReceiver, [_A1], R], arg1: _A1, /) -> R: ...
    @overload
    def __call__(
        self: Alternatives[_NoReceiver, [_A1, _A2], R], arg1: _A1, arg2: _A2, /
    ) -> R: ...
    @overload
    def __call__(
        self: Alternatives[_NoReceiver, [_A1, _A2, _A3], R],
        arg1: _A1,
        arg2: _A2,
        arg3: _A3,
        /,
    ) -> R: ...
    @overload
    def __call__(
        self: Alternatives[_NoReceiver, [_A1, _A2, _A3, _A4], R],
        arg1: _A1,
        arg2: _A2,
        arg3: _A3,
        arg4: _A4,
        /,
    ) -> R: ...
    @overload
    def __call__(
        self: Alternatives[_NoReceiver, [_A1, _A2, _A3, _A4, _A5], R],
        arg1: _A1,
        arg2: _A2,
        arg3: _A3,
        arg4: _A4,
        arg5: _A5,
        /,
    ) -> R: ...
    @overload
    def __call__(self: Alternatives[S, [], R], receiver: S, /) -> R: ...
    @overload
    def __call__(self: Alternatives[S, [_A1], R], receiver: S, arg1: _A1, /) -> R: ...
    @overload
    def __call__(
        self: Alternatives[S, [_A1, _A2], R], receiver: S, arg1: _A1, arg2: _A2, /
    ) -> R: ...
    @overload
    def __call__(
        self: Alternatives[S, [_A1, _A2, _A3], R],
        receiver: S,
        arg1: _A1,
        arg2: _A2,
        arg3: _A3,
        /,
    ) -> R: ...
    @overload
    def __call__(
        self: Alternatives[S, [_A1, _A2, _A3, _A4], R],
        receiver: S,
        arg1: _A1,
        arg2: _A2,
        arg3: _A3,
        arg4: _A4,
        /,
    ) -> R: ...
    @overload
    def __call__(
        self: Alternatives[S, [_A1, _A2, _A3, _A4, _A5], R],
        receiver: S,
        arg1: _A1,
        arg2: _A2,
        arg3: _A3,
        arg4: _A4,
        arg5: _A5,
        /,
    ) -> R: ...
    @overload
    def __call__(
        self: Alternatives[_NoReceiver, P, R],
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> R: ...
    @overload
    def __call__(self, receiver: S, *args: P.args, **kwargs: P.kwargs) -> R: ...
    @overload
    def __get__(
        self, instance: None, owner: type[object] | None = None
    ) -> Alternatives[S, P, R]: ...
    @overload
    def __get__(
        self: Alternatives[_NoReceiver, P, R],
        instance: object,
        owner: type[object] | None = None,
    ) -> _BoundAlternatives[_NoReceiver, P, R]: ...
    @overload
    def __get__(
        self, instance: S, owner: type[object] | None = None
    ) -> _BoundAlternatives[S, P, R]: ...
    @overload
    def __get__(
        self, instance: object, owner: type[object] | None = None
    ) -> Callable[Concatenate[S, P], R]: ...
    def _binds_on_class_access(self) -> bool: ...
    def measure(
        self,
        /,
        operator: Callable[[R], M],
        *args: object,
        **kwargs: object,
    ) -> dict[Implementation[S, P, R], M]: ...
    @overload
    def pytest_parametrize(
        self,
        *,
        only_default: bool = False,
    ) -> Callable[[F], F]: ...
    @overload
    def pytest_parametrize(
        self,
        test: F,
        *,
        only_default: bool = False,
    ) -> F: ...
    @overload
    def pytest_parametrize_pairs(
        self,
        *,
        n_cache: int | None = 0,
        double_reference: bool = False,
        only_default: bool = False,
    ) -> Callable[[F], F]: ...
    @overload
    def pytest_parametrize_pairs(
        self,
        test: F,
        *,
        n_cache: int | None = 0,
        double_reference: bool = False,
        only_default: bool = False,
    ) -> F: ...

class Implementation(Generic[S, P, R]):
    __match_args__: tuple[str, str, str]
    alternatives: Alternatives[S, P, R]
    implementation: Callable[..., R] | _TypedDescriptor[P, R]
    label: str | None

    def __init__(
        self,
        alternatives: Alternatives[S, P, R],
        implementation: Callable[..., R] | _TypedDescriptor[P, R],
        label: str | None = None,
    ) -> None: ...
    def __post_init__(self) -> None: ...
    def __repr__(self) -> str: ...
    def __hash__(self) -> int: ...
    @overload
    def __call__(self: Implementation[_NoReceiver, [], R]) -> R: ...
    @overload
    def __call__(self: Implementation[_NoReceiver, [_A1], R], arg1: _A1, /) -> R: ...
    @overload
    def __call__(
        self: Implementation[_NoReceiver, [_A1, _A2], R], arg1: _A1, arg2: _A2, /
    ) -> R: ...
    @overload
    def __call__(
        self: Implementation[_NoReceiver, [_A1, _A2, _A3], R],
        arg1: _A1,
        arg2: _A2,
        arg3: _A3,
        /,
    ) -> R: ...
    @overload
    def __call__(
        self: Implementation[_NoReceiver, [_A1, _A2, _A3, _A4], R],
        arg1: _A1,
        arg2: _A2,
        arg3: _A3,
        arg4: _A4,
        /,
    ) -> R: ...
    @overload
    def __call__(
        self: Implementation[_NoReceiver, [_A1, _A2, _A3, _A4, _A5], R],
        arg1: _A1,
        arg2: _A2,
        arg3: _A3,
        arg4: _A4,
        arg5: _A5,
        /,
    ) -> R: ...
    @overload
    def __call__(self: Implementation[S, [], R], receiver: S, /) -> R: ...
    @overload
    def __call__(self: Implementation[S, [_A1], R], receiver: S, arg1: _A1, /) -> R: ...
    @overload
    def __call__(
        self: Implementation[S, [_A1, _A2], R], receiver: S, arg1: _A1, arg2: _A2, /
    ) -> R: ...
    @overload
    def __call__(
        self: Implementation[S, [_A1, _A2, _A3], R],
        receiver: S,
        arg1: _A1,
        arg2: _A2,
        arg3: _A3,
        /,
    ) -> R: ...
    @overload
    def __call__(
        self: Implementation[S, [_A1, _A2, _A3, _A4], R],
        receiver: S,
        arg1: _A1,
        arg2: _A2,
        arg3: _A3,
        arg4: _A4,
        /,
    ) -> R: ...
    @overload
    def __call__(
        self: Implementation[S, [_A1, _A2, _A3, _A4, _A5], R],
        receiver: S,
        arg1: _A1,
        arg2: _A2,
        arg3: _A3,
        arg4: _A4,
        arg5: _A5,
        /,
    ) -> R: ...
    @overload
    def __call__(
        self: Implementation[_NoReceiver, P, R],
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> R: ...
    @overload
    def __call__(self, receiver: S, *args: P.args, **kwargs: P.kwargs) -> R: ...
    @overload
    def __get__(
        self, instance: None, owner: type[object] | None = None
    ) -> Implementation[S, P, R]: ...
    @overload
    def __get__(
        self: Implementation[_NoReceiver, P, R],
        instance: object,
        owner: type[object] | None = None,
    ) -> _BoundImplementation[_NoReceiver, P, R]: ...
    @overload
    def __get__(
        self, instance: S, owner: type[object] | None = None
    ) -> _BoundImplementation[S, P, R]: ...
    @overload
    def __get__(
        self, instance: object, owner: type[object] | None = None
    ) -> Callable[Concatenate[S, P], R]: ...
    @overload
    def add(
        self: Implementation[_NoReceiver, P, R],
        implementation: Callable[P, R]
        | Callable[Concatenate[type[_Owner], P], R]
        | classmethod[_Owner, P, R]
        | staticmethod[P, R],
        *,
        default: bool = False,
    ) -> Implementation[_NoReceiver, P, R]: ...
    @overload
    def add(
        self,
        implementation: Callable[Concatenate[S, P], R] | Implementation[S, P, R],
        *,
        default: bool = False,
    ) -> Implementation[S, P, R]: ...
    @overload
    def add(
        self, *, default: bool = False
    ) -> Callable[[Callable[..., R]], Implementation[S, P, R]]: ...

@overload
def reference(
    implementation: classmethod[_Owner, P, R],
    *,
    default: bool = False,
) -> Alternatives[_NoReceiver, P, R]: ...
@overload
def reference(
    implementation: staticmethod[P, R],
    *,
    default: bool = False,
) -> Alternatives[_NoReceiver, P, R]: ...
@overload
def reference(
    implementation: Callable[Concatenate[type[_Owner], P], R],
    *,
    default: bool = False,
) -> Alternatives[_NoReceiver, P, R]: ...
@overload
def reference(
    implementation: Callable[Concatenate[S, P], R], *, default: bool = False
) -> Alternatives[S, P, R]: ...
@overload
def reference(
    implementation: Callable[P, R], *, default: bool = False
) -> Alternatives[_NoReceiver, P, R]: ...
@overload
def reference(*, default: bool = False) -> _ReferenceDecorator: ...
def _get_caller_path() -> str | None: ...
