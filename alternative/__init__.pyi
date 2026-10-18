from __future__ import annotations

import sys
from typing import (
    Callable,
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
_T = TypeVar("_T")
_S_contra = TypeVar("_S_contra", contravariant=True)
R = TypeVar("R")
R_co = TypeVar("R_co", covariant=True)
M = TypeVar("M")
S = TypeVar("S")
Q = ParamSpec("Q")
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

class _FunctionLike(Protocol[_S_contra, P, Q, R_co]):
    @overload
    def __call__(self, /, *args: Q.args, **kwargs: Q.kwargs) -> R_co: ...
    @overload
    def __call__(
        self, first: _S_contra, /, *args: P.args, **kwargs: P.kwargs
    ) -> R_co: ...

class _AddDecorator(Protocol[S, P, R, Q]):
    @overload
    def __call__(
        self: _AddDecorator[_NoReceiver, P, R, P],
        implementation: classmethod[_Owner, P, R] | staticmethod[P, R],
        /,
    ) -> Implementation[_NoReceiver, P, R, P]: ...
    @overload
    def __call__(
        self,
        implementation: Callable[Q, R]
        | Implementation[S, P, R, Q]
        | Alternatives[S, P, R, Q],
        /,
    ) -> Implementation[S, P, R, Q]: ...

class _ReferenceDecorator(Protocol):
    @overload
    def __call__(
        self, implementation: classmethod[_Owner, P, R], /
    ) -> Alternatives[_NoReceiver, P, R, P]: ...
    @overload
    def __call__(
        self, implementation: staticmethod[P, R], /
    ) -> Alternatives[_NoReceiver, P, R, P]: ...
    @overload
    def __call__(
        self, implementation: _FunctionLike[S, P, Q, R], /
    ) -> Alternatives[S, P, R, Q]: ...
    @overload
    def __call__(
        self, implementation: Callable[Q, R], /
    ) -> Alternatives[_NoReceiver, Q, R, Q]: ...

class AlternativeError(Exception):
    """Base class for all alternative errors."""

class AddTooLateError(AlternativeError):
    """Cannot add implementations after the alternatives have been invoked."""

class MultipleDefaultsError(AlternativeError):
    """Cannot set the default implementation more than once."""

class CrossAlternativesImplementationError(AlternativeError):
    """Cannot add an Implementation object that belongs to a different Alternatives set."""

class _BoundAlternatives(Generic[S, P, R, Q]):
    __match_args__: tuple[str, str, str]
    alternatives: Alternatives[S, P, R, Q]
    instance: object | None
    owner: type[object] | None
    if sys.version_info >= (3, 13):
        def __replace__(
            self, /, **changes: object
        ) -> _BoundAlternatives[S, P, R, Q]: ...
    def __init__(
        self,
        alternatives: Alternatives[S, P, R, Q],
        instance: object | None,
        owner: type[object] | None,
    ) -> None: ...
    @overload
    def __call__(self: _BoundAlternatives[S, [], R, Q]) -> R: ...
    @overload
    def __call__(self: _BoundAlternatives[S, [_A1], R, Q], arg1: _A1, /) -> R: ...
    @overload
    def __call__(
        self: _BoundAlternatives[S, [_A1, _A2], R, Q], arg1: _A1, arg2: _A2, /
    ) -> R: ...
    @overload
    def __call__(
        self: _BoundAlternatives[S, [_A1, _A2, _A3], R, Q],
        arg1: _A1,
        arg2: _A2,
        arg3: _A3,
        /,
    ) -> R: ...
    @overload
    def __call__(
        self: _BoundAlternatives[S, [_A1, _A2, _A3, _A4], R, Q],
        arg1: _A1,
        arg2: _A2,
        arg3: _A3,
        arg4: _A4,
        /,
    ) -> R: ...
    @overload
    def __call__(
        self: _BoundAlternatives[S, [_A1, _A2, _A3, _A4, _A5], R, Q],
        arg1: _A1,
        arg2: _A2,
        arg3: _A3,
        arg4: _A4,
        arg5: _A5,
        /,
    ) -> R: ...
    @overload
    def __call__(self, /, *args: P.args, **kwargs: P.kwargs) -> R: ...
    @overload
    def add(
        self: _BoundAlternatives[_NoReceiver, P, R, P],
        implementation: classmethod[_Owner, P, R] | staticmethod[P, R] | Callable[P, R],
        *,
        default: bool = False,
    ) -> Implementation[_NoReceiver, P, R, P]: ...
    @overload
    def add(
        self,
        implementation: Callable[Q, R]
        | Implementation[S, P, R, Q]
        | Alternatives[S, P, R, Q],
        *,
        default: bool = False,
    ) -> Implementation[S, P, R, Q]: ...
    @overload
    def add(self, *, default: bool = False) -> _AddDecorator[S, P, R, Q]: ...
    @property
    def implementations(self) -> tuple[Implementation[S, P, R, Q], ...]: ...
    @property
    def reference(self) -> Implementation[S, P, R, Q]: ...
    @property
    def callable(self) -> Callable[Q, R] | _TypedDescriptor[P, R]: ...
    @overload
    def pytest_parametrize(self, *, only_default: bool = False) -> Callable[[F], F]: ...
    @overload
    def pytest_parametrize(self, test: F, *, only_default: bool = False) -> F: ...
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

class _BoundImplementation(Generic[S, P, R, Q]):
    __match_args__: tuple[str, str, str]
    implementation: Implementation[S, P, R, Q]
    instance: object | None
    owner: type[object] | None
    if sys.version_info >= (3, 13):
        def __replace__(
            self, /, **changes: object
        ) -> _BoundImplementation[S, P, R, Q]: ...
    def __init__(
        self,
        implementation: Implementation[S, P, R, Q],
        instance: object | None,
        owner: type[object] | None,
    ) -> None: ...
    @overload
    def __call__(self: _BoundImplementation[S, [], R, Q]) -> R: ...
    @overload
    def __call__(self: _BoundImplementation[S, [_A1], R, Q], arg1: _A1, /) -> R: ...
    @overload
    def __call__(
        self: _BoundImplementation[S, [_A1, _A2], R, Q], arg1: _A1, arg2: _A2, /
    ) -> R: ...
    @overload
    def __call__(
        self: _BoundImplementation[S, [_A1, _A2, _A3], R, Q],
        arg1: _A1,
        arg2: _A2,
        arg3: _A3,
        /,
    ) -> R: ...
    @overload
    def __call__(
        self: _BoundImplementation[S, [_A1, _A2, _A3, _A4], R, Q],
        arg1: _A1,
        arg2: _A2,
        arg3: _A3,
        arg4: _A4,
        /,
    ) -> R: ...
    @overload
    def __call__(
        self: _BoundImplementation[S, [_A1, _A2, _A3, _A4, _A5], R, Q],
        arg1: _A1,
        arg2: _A2,
        arg3: _A3,
        arg4: _A4,
        arg5: _A5,
        /,
    ) -> R: ...
    @overload
    def __call__(self, /, *args: P.args, **kwargs: P.kwargs) -> R: ...
    @overload
    def add(
        self: _BoundImplementation[_NoReceiver, P, R, P],
        implementation: classmethod[_Owner, P, R] | staticmethod[P, R] | Callable[P, R],
        *,
        default: bool = False,
    ) -> Implementation[_NoReceiver, P, R, P]: ...
    @overload
    def add(
        self,
        implementation: Callable[Q, R]
        | Implementation[S, P, R, Q]
        | Alternatives[S, P, R, Q],
        *,
        default: bool = False,
    ) -> Implementation[S, P, R, Q]: ...
    @overload
    def add(self, *, default: bool = False) -> _AddDecorator[S, P, R, Q]: ...
    @property
    def alternatives(self) -> Alternatives[S, P, R, Q]: ...

class Alternatives(Generic[S, P, R, Q]):
    _reference: Implementation[S, P, R, Q]
    _default: Implementation[S, P, R, Q] | None
    _debug_default: str | None
    _invoked: bool
    _debug_invoked_site: str | None
    _enumerated: bool
    _callable: Callable[..., R] | _TypedDescriptor[P, R] | None
    _debug_callable_used: str | None
    _implementations: list[Implementation[S, P, R, Q]]
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
        self: Alternatives[_NoReceiver, P, R, P],
        implementation: classmethod[_Owner, P, R] | staticmethod[P, R] | Callable[P, R],
        *,
        default: bool = False,
    ) -> Implementation[_NoReceiver, P, R, P]: ...
    @overload
    def add(
        self,
        implementation: Callable[Q, R]
        | Implementation[S, P, R, Q]
        | Alternatives[S, P, R, Q],
        *,
        default: bool = False,
    ) -> Implementation[S, P, R, Q]: ...
    @overload
    def add(self, *, default: bool = False) -> _AddDecorator[S, P, R, Q]: ...
    @property
    def reference(self) -> Implementation[S, P, R, Q]: ...
    @property
    def callable(self) -> Callable[Q, R] | _TypedDescriptor[P, R]: ...
    @property
    def implementations(self) -> tuple[Implementation[S, P, R, Q], ...]: ...
    @overload
    def __call__(self: Alternatives[S, P, R, []]) -> R: ...
    @overload
    def __call__(self: Alternatives[S, P, R, [_A1]], arg1: _A1, /) -> R: ...
    @overload
    def __call__(
        self: Alternatives[S, P, R, [_A1, _A2]], arg1: _A1, arg2: _A2, /
    ) -> R: ...
    @overload
    def __call__(
        self: Alternatives[S, P, R, [_A1, _A2, _A3]], arg1: _A1, arg2: _A2, arg3: _A3, /
    ) -> R: ...
    @overload
    def __call__(
        self: Alternatives[S, P, R, [_A1, _A2, _A3, _A4]],
        arg1: _A1,
        arg2: _A2,
        arg3: _A3,
        arg4: _A4,
        /,
    ) -> R: ...
    @overload
    def __call__(
        self: Alternatives[S, P, R, [_A1, _A2, _A3, _A4, _A5]],
        arg1: _A1,
        arg2: _A2,
        arg3: _A3,
        arg4: _A4,
        arg5: _A5,
        /,
    ) -> R: ...
    @overload
    def __call__(self, /, *args: Q.args, **kwargs: Q.kwargs) -> R: ...
    @overload
    def __get__(
        self: Alternatives[type[_T], P, R, Q], instance: None, owner: type[_T]
    ) -> _BoundAlternatives[type[_T], P, R, Q]: ...
    @overload
    def __get__(
        self: Alternatives[type[_T], P, R, Q],
        instance: _T,
        owner: type[_T] | None = None,
    ) -> _BoundAlternatives[type[_T], P, R, Q]: ...
    @overload
    def __get__(
        self, instance: None, owner: type[object] | None = None
    ) -> Alternatives[S, P, R, Q]: ...
    @overload
    def __get__(
        self: Alternatives[_NoReceiver, P, R, P],
        instance: object,
        owner: type[object] | None = None,
    ) -> _BoundAlternatives[_NoReceiver, P, R, P]: ...
    @overload
    def __get__(
        self, instance: S, owner: type[object] | None = None
    ) -> _BoundAlternatives[S, P, R, Q]: ...
    @overload
    def __get__(
        self, instance: object, owner: type[object] | None = None
    ) -> Alternatives[S, P, R, Q]: ...
    def _binds_on_class_access(self) -> bool: ...
    def measure(
        self: Alternatives[S, P, R, Q],
        /,
        operator: Callable[[R], M],
        *args: Q.args,
        **kwargs: Q.kwargs,
    ) -> dict[Implementation[S, P, R, Q], M]: ...
    @overload
    def pytest_parametrize(self, *, only_default: bool = False) -> Callable[[F], F]: ...
    @overload
    def pytest_parametrize(self, test: F, *, only_default: bool = False) -> F: ...
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

class Implementation(Generic[S, P, R, Q]):
    __match_args__: tuple[str, str, str]
    alternatives: Alternatives[S, P, R, Q]
    implementation: Callable[..., R] | _TypedDescriptor[P, R]
    label: str | None

    if sys.version_info >= (3, 13):
        def __replace__(self, /, **changes: object) -> Implementation[S, P, R, Q]: ...
    def __init__(
        self,
        alternatives: Alternatives[S, P, R, Q],
        implementation: Callable[..., R] | _TypedDescriptor[P, R],
        label: str | None = None,
    ) -> None: ...
    def __post_init__(self) -> None: ...
    def __repr__(self) -> str: ...
    def __hash__(self) -> int: ...
    @overload
    def __call__(self: Implementation[S, P, R, []]) -> R: ...
    @overload
    def __call__(self: Implementation[S, P, R, [_A1]], arg1: _A1, /) -> R: ...
    @overload
    def __call__(
        self: Implementation[S, P, R, [_A1, _A2]], arg1: _A1, arg2: _A2, /
    ) -> R: ...
    @overload
    def __call__(
        self: Implementation[S, P, R, [_A1, _A2, _A3]],
        arg1: _A1,
        arg2: _A2,
        arg3: _A3,
        /,
    ) -> R: ...
    @overload
    def __call__(
        self: Implementation[S, P, R, [_A1, _A2, _A3, _A4]],
        arg1: _A1,
        arg2: _A2,
        arg3: _A3,
        arg4: _A4,
        /,
    ) -> R: ...
    @overload
    def __call__(
        self: Implementation[S, P, R, [_A1, _A2, _A3, _A4, _A5]],
        arg1: _A1,
        arg2: _A2,
        arg3: _A3,
        arg4: _A4,
        arg5: _A5,
        /,
    ) -> R: ...
    @overload
    def __call__(self, /, *args: Q.args, **kwargs: Q.kwargs) -> R: ...
    @overload
    def __get__(
        self: Implementation[type[_T], P, R, Q],
        instance: None,
        owner: type[_T],
    ) -> _BoundImplementation[type[_T], P, R, Q]: ...
    @overload
    def __get__(
        self: Implementation[type[_T], P, R, Q],
        instance: _T,
        owner: type[_T] | None = None,
    ) -> _BoundImplementation[type[_T], P, R, Q]: ...
    @overload
    def __get__(
        self, instance: None, owner: type[object] | None = None
    ) -> Implementation[S, P, R, Q]: ...
    @overload
    def __get__(
        self: Implementation[_NoReceiver, P, R, P],
        instance: object,
        owner: type[object] | None = None,
    ) -> _BoundImplementation[_NoReceiver, P, R, P]: ...
    @overload
    def __get__(
        self, instance: S, owner: type[object] | None = None
    ) -> _BoundImplementation[S, P, R, Q]: ...
    @overload
    def __get__(
        self, instance: object, owner: type[object] | None = None
    ) -> Implementation[S, P, R, Q]: ...
    @overload
    def add(
        self: Implementation[_NoReceiver, P, R, P],
        implementation: classmethod[_Owner, P, R] | staticmethod[P, R] | Callable[P, R],
        *,
        default: bool = False,
    ) -> Implementation[_NoReceiver, P, R, P]: ...
    @overload
    def add(
        self,
        implementation: Callable[Q, R]
        | Implementation[S, P, R, Q]
        | Alternatives[S, P, R, Q],
        *,
        default: bool = False,
    ) -> Implementation[S, P, R, Q]: ...
    @overload
    def add(self, *, default: bool = False) -> _AddDecorator[S, P, R, Q]: ...

@overload
def reference(
    implementation: classmethod[_Owner, P, R], *, default: bool = False
) -> Alternatives[_NoReceiver, P, R, P]: ...
@overload
def reference(
    implementation: staticmethod[P, R], *, default: bool = False
) -> Alternatives[_NoReceiver, P, R, P]: ...
@overload
def reference(
    implementation: _FunctionLike[S, P, Q, R], *, default: bool = False
) -> Alternatives[S, P, R, Q]: ...
@overload
def reference(
    implementation: Callable[Q, R], *, default: bool = False
) -> Alternatives[_NoReceiver, Q, R, Q]: ...
@overload
def reference(*, default: bool = False) -> _ReferenceDecorator: ...
def _get_caller_path() -> str | None: ...
