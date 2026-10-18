import sys
from collections.abc import Callable
from typing import (
    Concatenate,
    Generic,
    ParamSpec,
    Protocol,
    TypeVar,
    overload,
)

DEBUG: bool

__all__ = [
    "AddTooLateError",
    "AlternativeError",
    "Alternatives",
    "CrossAlternativesImplementationError",
    "Implementation",
    "MultipleDefaultsError",
    "reference",
]

_P = ParamSpec("_P")
_R = TypeVar("_R")
_R_co = TypeVar("_R_co", covariant=True)
_M = TypeVar("_M")
_S = TypeVar("_S")
_Owner = TypeVar("_Owner")
_F = TypeVar("_F", bound=Callable[..., object])
_A1 = TypeVar("_A1")
_A2 = TypeVar("_A2")
_A3 = TypeVar("_A3")
_A4 = TypeVar("_A4")
_A5 = TypeVar("_A5")

class _NoReceiver:
    """Marker type for descriptors that bind themselves before user calls."""

class _TypedDescriptor(Protocol[_P, _R_co]):
    def __get__(
        self, instance: object | None, owner: type[object] | None = None, /
    ) -> Callable[_P, _R_co]: ...

class _AddDecorator(Protocol[_S, _P, _R]):
    @overload
    def __call__(
        self: _AddDecorator[_NoReceiver, _P, _R],
        implementation: Callable[_P, _R]
        | Callable[Concatenate[type[_Owner], _P], _R]
        | classmethod[_Owner, _P, _R]
        | staticmethod[_P, _R],
        /,
    ) -> Implementation[_NoReceiver, _P, _R]: ...
    @overload
    def __call__(
        self,
        implementation: Callable[Concatenate[_S, _P], _R] | Implementation[_S, _P, _R],
        /,
    ) -> Implementation[_S, _P, _R]: ...

class _ReferenceDecorator(Protocol):
    @overload
    def __call__(
        self,
        implementation: classmethod[_Owner, _P, _R],
        /,
    ) -> Alternatives[_NoReceiver, _P, _R]: ...
    @overload
    def __call__(
        self,
        implementation: staticmethod[_P, _R],
        /,
    ) -> Alternatives[_NoReceiver, _P, _R]: ...
    @overload
    def __call__(
        self, implementation: Callable[Concatenate[type[_Owner], _P], _R], /
    ) -> Alternatives[_NoReceiver, _P, _R]: ...
    @overload
    def __call__(
        self, implementation: Callable[Concatenate[_S, _P], _R], /
    ) -> Alternatives[_S, _P, _R]: ...
    @overload
    def __call__(
        self, implementation: Callable[_P, _R], /
    ) -> Alternatives[_NoReceiver, _P, _R]: ...

class AlternativeError(Exception):
    """Base class for all alternative errors."""

class AddTooLateError(AlternativeError):
    """Cannot add implementations after the alternatives have been invoked."""

class MultipleDefaultsError(AlternativeError):
    """Cannot set the default implementation more than once."""

class CrossAlternativesImplementationError(AlternativeError):
    """Cannot add an Implementation object that belongs to a different Alternatives set."""

class _BoundAlternatives(Generic[_S, _P, _R]):
    __match_args__ = ("alternatives", "instance", "owner")
    alternatives: Alternatives[_S, _P, _R]
    instance: object | None
    owner: type[object] | None

    if sys.version_info >= (3, 13):
        def __replace__(
            self, /, **changes: object
        ) -> _BoundAlternatives[_S, _P, _R]: ...

    def __init__(
        self,
        alternatives: Alternatives[_S, _P, _R],
        instance: object | None,
        owner: type[object] | None,
    ) -> None: ...
    @overload
    def __call__(self: _BoundAlternatives[_S, [], _R]) -> _R: ...
    @overload
    def __call__(self: _BoundAlternatives[_S, [_A1], _R], arg1: _A1, /) -> _R: ...
    @overload
    def __call__(
        self: _BoundAlternatives[_S, [_A1, _A2], _R], arg1: _A1, arg2: _A2, /
    ) -> _R: ...
    @overload
    def __call__(
        self: _BoundAlternatives[_S, [_A1, _A2, _A3], _R],
        arg1: _A1,
        arg2: _A2,
        arg3: _A3,
        /,
    ) -> _R: ...
    @overload
    def __call__(
        self: _BoundAlternatives[_S, [_A1, _A2, _A3, _A4], _R],
        arg1: _A1,
        arg2: _A2,
        arg3: _A3,
        arg4: _A4,
        /,
    ) -> _R: ...
    @overload
    def __call__(
        self: _BoundAlternatives[_S, [_A1, _A2, _A3, _A4, _A5], _R],
        arg1: _A1,
        arg2: _A2,
        arg3: _A3,
        arg4: _A4,
        arg5: _A5,
        /,
    ) -> _R: ...
    @overload
    def __call__(self, *args: _P.args, **kwargs: _P.kwargs) -> _R: ...
    @overload
    def add(
        self: _BoundAlternatives[_NoReceiver, _P, _R],
        implementation: Callable[_P, _R]
        | Callable[Concatenate[type[_Owner], _P], _R]
        | classmethod[_Owner, _P, _R]
        | staticmethod[_P, _R],
        *,
        default: bool = False,
    ) -> Implementation[_NoReceiver, _P, _R]: ...
    @overload
    def add(
        self,
        implementation: Callable[Concatenate[_S, _P], _R] | Implementation[_S, _P, _R],
        *,
        default: bool = False,
    ) -> Implementation[_S, _P, _R]: ...
    @overload
    def add(self, *, default: bool = False) -> _AddDecorator[_S, _P, _R]: ...
    @property
    def implementations(self) -> tuple[Implementation[_S, _P, _R], ...]: ...
    @property
    def reference(self) -> Implementation[_S, _P, _R]: ...
    @property
    def callable(self) -> Callable[..., _R] | _TypedDescriptor[_P, _R]: ...
    @overload
    def pytest_parametrize(
        self, *, only_default: bool = False
    ) -> Callable[[_F], _F]: ...
    @overload
    def pytest_parametrize(self, test: _F, *, only_default: bool = False) -> _F: ...
    @overload
    def pytest_parametrize_pairs(
        self,
        *,
        n_cache: int | None = 0,
        double_reference: bool = False,
        only_default: bool = False,
    ) -> Callable[[_F], _F]: ...
    @overload
    def pytest_parametrize_pairs(
        self,
        test: _F,
        *,
        n_cache: int | None = 0,
        double_reference: bool = False,
        only_default: bool = False,
    ) -> _F: ...

class _BoundImplementation(Generic[_S, _P, _R]):
    __match_args__ = ("implementation", "instance", "owner")
    implementation: Implementation[_S, _P, _R]
    instance: object | None
    owner: type[object] | None

    if sys.version_info >= (3, 13):
        def __replace__(
            self, /, **changes: object
        ) -> _BoundImplementation[_S, _P, _R]: ...

    def __init__(
        self,
        implementation: Implementation[_S, _P, _R],
        instance: object | None,
        owner: type[object] | None,
    ) -> None: ...
    @overload
    def __call__(self: _BoundImplementation[_S, [], _R]) -> _R: ...
    @overload
    def __call__(self: _BoundImplementation[_S, [_A1], _R], arg1: _A1, /) -> _R: ...
    @overload
    def __call__(
        self: _BoundImplementation[_S, [_A1, _A2], _R], arg1: _A1, arg2: _A2, /
    ) -> _R: ...
    @overload
    def __call__(
        self: _BoundImplementation[_S, [_A1, _A2, _A3], _R],
        arg1: _A1,
        arg2: _A2,
        arg3: _A3,
        /,
    ) -> _R: ...
    @overload
    def __call__(
        self: _BoundImplementation[_S, [_A1, _A2, _A3, _A4], _R],
        arg1: _A1,
        arg2: _A2,
        arg3: _A3,
        arg4: _A4,
        /,
    ) -> _R: ...
    @overload
    def __call__(
        self: _BoundImplementation[_S, [_A1, _A2, _A3, _A4, _A5], _R],
        arg1: _A1,
        arg2: _A2,
        arg3: _A3,
        arg4: _A4,
        arg5: _A5,
        /,
    ) -> _R: ...
    @overload
    def __call__(self, *args: _P.args, **kwargs: _P.kwargs) -> _R: ...
    @property
    def alternatives(self) -> Alternatives[_S, _P, _R]: ...
    @overload
    def add(
        self: _BoundImplementation[_NoReceiver, _P, _R],
        implementation: Callable[_P, _R]
        | Callable[Concatenate[type[_Owner], _P], _R]
        | classmethod[_Owner, _P, _R]
        | staticmethod[_P, _R],
        *,
        default: bool = False,
    ) -> Implementation[_NoReceiver, _P, _R]: ...
    @overload
    def add(
        self,
        implementation: Callable[Concatenate[_S, _P], _R] | Implementation[_S, _P, _R],
        *,
        default: bool = False,
    ) -> Implementation[_S, _P, _R]: ...
    @overload
    def add(self, *, default: bool = False) -> _AddDecorator[_S, _P, _R]: ...

class Alternatives(Generic[_S, _P, _R]):
    _reference: Implementation[_S, _P, _R]
    _default: Implementation[_S, _P, _R] | None
    _debug_default: str | None
    _invoked: bool
    _debug_invoked_site: str | None
    _enumerated: bool
    _callable: Callable[..., _R] | _TypedDescriptor[_P, _R] | None
    _debug_callable_used: str | None
    _implementations: list[Implementation[_S, _P, _R]]
    _implementations_used: bool
    _debug_implementations_used: str | None

    def __init__(
        self,
        implementation: Callable[..., _R] | _TypedDescriptor[_P, _R],
        *,
        default: bool = False,
    ) -> None: ...
    @overload
    def add(
        self: Alternatives[_NoReceiver, _P, _R],
        implementation: Callable[_P, _R]
        | Callable[Concatenate[type[_Owner], _P], _R]
        | classmethod[_Owner, _P, _R]
        | staticmethod[_P, _R],
        *,
        default: bool = False,
    ) -> Implementation[_NoReceiver, _P, _R]: ...
    @overload
    def add(
        self,
        implementation: Callable[Concatenate[_S, _P], _R] | Implementation[_S, _P, _R],
        *,
        default: bool = False,
    ) -> Implementation[_S, _P, _R]: ...
    @overload
    def add(self, *, default: bool = False) -> _AddDecorator[_S, _P, _R]: ...
    @property
    def reference(self) -> Implementation[_S, _P, _R]: ...
    @property
    def callable(self) -> Callable[..., _R] | _TypedDescriptor[_P, _R]: ...
    @property
    def implementations(self) -> tuple[Implementation[_S, _P, _R], ...]: ...
    @overload
    def __call__(self: Alternatives[_NoReceiver, [], _R]) -> _R: ...
    @overload
    def __call__(self: Alternatives[_NoReceiver, [_A1], _R], arg1: _A1, /) -> _R: ...
    @overload
    def __call__(
        self: Alternatives[_NoReceiver, [_A1, _A2], _R], arg1: _A1, arg2: _A2, /
    ) -> _R: ...
    @overload
    def __call__(
        self: Alternatives[_NoReceiver, [_A1, _A2, _A3], _R],
        arg1: _A1,
        arg2: _A2,
        arg3: _A3,
        /,
    ) -> _R: ...
    @overload
    def __call__(
        self: Alternatives[_NoReceiver, [_A1, _A2, _A3, _A4], _R],
        arg1: _A1,
        arg2: _A2,
        arg3: _A3,
        arg4: _A4,
        /,
    ) -> _R: ...
    @overload
    def __call__(
        self: Alternatives[_NoReceiver, [_A1, _A2, _A3, _A4, _A5], _R],
        arg1: _A1,
        arg2: _A2,
        arg3: _A3,
        arg4: _A4,
        arg5: _A5,
        /,
    ) -> _R: ...
    @overload
    def __call__(self: Alternatives[_S, [], _R], receiver: _S, /) -> _R: ...
    @overload
    def __call__(
        self: Alternatives[_S, [_A1], _R], receiver: _S, arg1: _A1, /
    ) -> _R: ...
    @overload
    def __call__(
        self: Alternatives[_S, [_A1, _A2], _R], receiver: _S, arg1: _A1, arg2: _A2, /
    ) -> _R: ...
    @overload
    def __call__(
        self: Alternatives[_S, [_A1, _A2, _A3], _R],
        receiver: _S,
        arg1: _A1,
        arg2: _A2,
        arg3: _A3,
        /,
    ) -> _R: ...
    @overload
    def __call__(
        self: Alternatives[_S, [_A1, _A2, _A3, _A4], _R],
        receiver: _S,
        arg1: _A1,
        arg2: _A2,
        arg3: _A3,
        arg4: _A4,
        /,
    ) -> _R: ...
    @overload
    def __call__(
        self: Alternatives[_S, [_A1, _A2, _A3, _A4, _A5], _R],
        receiver: _S,
        arg1: _A1,
        arg2: _A2,
        arg3: _A3,
        arg4: _A4,
        arg5: _A5,
        /,
    ) -> _R: ...
    @overload
    def __call__(
        self: Alternatives[_NoReceiver, _P, _R],
        *args: _P.args,
        **kwargs: _P.kwargs,
    ) -> _R: ...
    @overload
    def __call__(self, receiver: _S, *args: _P.args, **kwargs: _P.kwargs) -> _R: ...
    @overload
    def __get__(
        self, instance: None, owner: type[object] | None = None
    ) -> Alternatives[_S, _P, _R]: ...
    @overload
    def __get__(
        self: Alternatives[_NoReceiver, _P, _R],
        instance: object,
        owner: type[object] | None = None,
    ) -> _BoundAlternatives[_NoReceiver, _P, _R]: ...
    @overload
    def __get__(
        self, instance: _S, owner: type[object] | None = None
    ) -> _BoundAlternatives[_S, _P, _R]: ...
    @overload
    def __get__(
        self, instance: object, owner: type[object] | None = None
    ) -> Callable[Concatenate[_S, _P], _R]: ...
    def _binds_on_class_access(self) -> bool: ...
    def measure(
        self,
        /,
        operator: Callable[[_R], _M],
        *args: object,
        **kwargs: object,
    ) -> dict[Implementation[_S, _P, _R], _M]: ...
    @overload
    def pytest_parametrize(
        self,
        *,
        only_default: bool = False,
    ) -> Callable[[_F], _F]: ...
    @overload
    def pytest_parametrize(
        self,
        test: _F,
        *,
        only_default: bool = False,
    ) -> _F: ...
    @overload
    def pytest_parametrize_pairs(
        self,
        *,
        n_cache: int | None = 0,
        double_reference: bool = False,
        only_default: bool = False,
    ) -> Callable[[_F], _F]: ...
    @overload
    def pytest_parametrize_pairs(
        self,
        test: _F,
        *,
        n_cache: int | None = 0,
        double_reference: bool = False,
        only_default: bool = False,
    ) -> _F: ...

class Implementation(Generic[_S, _P, _R]):
    __match_args__ = ("alternatives", "implementation", "label")
    alternatives: Alternatives[_S, _P, _R]
    implementation: Callable[..., _R] | _TypedDescriptor[_P, _R]
    label: str | None

    if sys.version_info >= (3, 13):
        def __replace__(self, /, **changes: object) -> Implementation[_S, _P, _R]: ...
    def __init__(
        self,
        alternatives: Alternatives[_S, _P, _R],
        implementation: Callable[..., _R] | _TypedDescriptor[_P, _R],
        label: str | None = None,
    ) -> None: ...
    def __post_init__(self) -> None: ...
    def __hash__(self) -> int: ...
    @overload
    def __call__(self: Implementation[_NoReceiver, [], _R]) -> _R: ...
    @overload
    def __call__(self: Implementation[_NoReceiver, [_A1], _R], arg1: _A1, /) -> _R: ...
    @overload
    def __call__(
        self: Implementation[_NoReceiver, [_A1, _A2], _R], arg1: _A1, arg2: _A2, /
    ) -> _R: ...
    @overload
    def __call__(
        self: Implementation[_NoReceiver, [_A1, _A2, _A3], _R],
        arg1: _A1,
        arg2: _A2,
        arg3: _A3,
        /,
    ) -> _R: ...
    @overload
    def __call__(
        self: Implementation[_NoReceiver, [_A1, _A2, _A3, _A4], _R],
        arg1: _A1,
        arg2: _A2,
        arg3: _A3,
        arg4: _A4,
        /,
    ) -> _R: ...
    @overload
    def __call__(
        self: Implementation[_NoReceiver, [_A1, _A2, _A3, _A4, _A5], _R],
        arg1: _A1,
        arg2: _A2,
        arg3: _A3,
        arg4: _A4,
        arg5: _A5,
        /,
    ) -> _R: ...
    @overload
    def __call__(self: Implementation[_S, [], _R], receiver: _S, /) -> _R: ...
    @overload
    def __call__(
        self: Implementation[_S, [_A1], _R], receiver: _S, arg1: _A1, /
    ) -> _R: ...
    @overload
    def __call__(
        self: Implementation[_S, [_A1, _A2], _R], receiver: _S, arg1: _A1, arg2: _A2, /
    ) -> _R: ...
    @overload
    def __call__(
        self: Implementation[_S, [_A1, _A2, _A3], _R],
        receiver: _S,
        arg1: _A1,
        arg2: _A2,
        arg3: _A3,
        /,
    ) -> _R: ...
    @overload
    def __call__(
        self: Implementation[_S, [_A1, _A2, _A3, _A4], _R],
        receiver: _S,
        arg1: _A1,
        arg2: _A2,
        arg3: _A3,
        arg4: _A4,
        /,
    ) -> _R: ...
    @overload
    def __call__(
        self: Implementation[_S, [_A1, _A2, _A3, _A4, _A5], _R],
        receiver: _S,
        arg1: _A1,
        arg2: _A2,
        arg3: _A3,
        arg4: _A4,
        arg5: _A5,
        /,
    ) -> _R: ...
    @overload
    def __call__(
        self: Implementation[_NoReceiver, _P, _R],
        *args: _P.args,
        **kwargs: _P.kwargs,
    ) -> _R: ...
    @overload
    def __call__(self, receiver: _S, *args: _P.args, **kwargs: _P.kwargs) -> _R: ...
    @overload
    def __get__(
        self, instance: None, owner: type[object] | None = None
    ) -> Implementation[_S, _P, _R]: ...
    @overload
    def __get__(
        self: Implementation[_NoReceiver, _P, _R],
        instance: object,
        owner: type[object] | None = None,
    ) -> _BoundImplementation[_NoReceiver, _P, _R]: ...
    @overload
    def __get__(
        self, instance: _S, owner: type[object] | None = None
    ) -> _BoundImplementation[_S, _P, _R]: ...
    @overload
    def __get__(
        self, instance: object, owner: type[object] | None = None
    ) -> Callable[Concatenate[_S, _P], _R]: ...
    @overload
    def add(
        self: Implementation[_NoReceiver, _P, _R],
        implementation: Callable[_P, _R]
        | Callable[Concatenate[type[_Owner], _P], _R]
        | classmethod[_Owner, _P, _R]
        | staticmethod[_P, _R],
        *,
        default: bool = False,
    ) -> Implementation[_NoReceiver, _P, _R]: ...
    @overload
    def add(
        self,
        implementation: Callable[Concatenate[_S, _P], _R] | Implementation[_S, _P, _R],
        *,
        default: bool = False,
    ) -> Implementation[_S, _P, _R]: ...
    @overload
    def add(self, *, default: bool = False) -> _AddDecorator[_S, _P, _R]: ...

@overload
def reference(
    implementation: classmethod[_Owner, _P, _R],
    *,
    default: bool = False,
) -> Alternatives[_NoReceiver, _P, _R]: ...
@overload
def reference(
    implementation: staticmethod[_P, _R],
    *,
    default: bool = False,
) -> Alternatives[_NoReceiver, _P, _R]: ...
@overload
def reference(
    implementation: Callable[Concatenate[type[_Owner], _P], _R],
    *,
    default: bool = False,
) -> Alternatives[_NoReceiver, _P, _R]: ...
@overload
def reference(
    implementation: Callable[Concatenate[_S, _P], _R], *, default: bool = False
) -> Alternatives[_S, _P, _R]: ...
@overload
def reference(
    implementation: Callable[_P, _R], *, default: bool = False
) -> Alternatives[_NoReceiver, _P, _R]: ...
@overload
def reference(*, default: bool = False) -> _ReferenceDecorator: ...
def _get_caller_path() -> str | None: ...
