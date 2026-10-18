import sys
from collections.abc import Callable
from typing import (
    Generic,
    ParamSpec,
    Protocol,
    TypeAlias,
    TypeVar,
    overload,
    type_check_only,
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
_T = TypeVar("_T")
_S_contra = TypeVar("_S_contra", contravariant=True)
_R = TypeVar("_R")
_R_co = TypeVar("_R_co", covariant=True)
_M = TypeVar("_M")
_S = TypeVar("_S")
_Q = ParamSpec("_Q")
_Owner = TypeVar("_Owner")
_F = TypeVar("_F", bound=Callable[..., object])
_A1 = TypeVar("_A1")
_A2 = TypeVar("_A2")
_A3 = TypeVar("_A3")
_A4 = TypeVar("_A4")
_A5 = TypeVar("_A5")

@type_check_only
class _NoReceiver:
    """Marker type for descriptors that bind themselves before user calls."""

class _TypedDescriptor(Protocol[_P, _R_co]):
    def __get__(
        self, instance: object | None, owner: type[object] | None = None, /
    ) -> Callable[_P, _R_co]: ...

_ImplementationSource: TypeAlias = _TypedDescriptor[_P, _R] | Callable[..., _R]
_RegistrationInput: TypeAlias = (
    Implementation[_S, _P, _R, _Q] | Alternatives[_S, _P, _R, _Q] | Callable[_Q, _R]
)

class _FunctionLike(Protocol[_S_contra, _P, _Q, _R_co]):
    @overload
    def __call__(self, /, *args: _Q.args, **kwargs: _Q.kwargs) -> _R_co: ...
    @overload
    def __call__(
        self, first: _S_contra, /, *args: _P.args, **kwargs: _P.kwargs
    ) -> _R_co: ...

class _AddDecorator(Protocol[_S, _P, _R, _Q]):
    @overload
    def __call__(
        self: _AddDecorator[_NoReceiver, _P, _R, _P],
        implementation: classmethod[_Owner, _P, _R] | staticmethod[_P, _R],
        /,
    ) -> Implementation[_NoReceiver, _P, _R, _P]: ...
    @overload
    def __call__(
        self,
        implementation: _RegistrationInput[_S, _P, _R, _Q],
        /,
    ) -> Implementation[_S, _P, _R, _Q]: ...

class _ReferenceDecorator(Protocol):
    @overload
    def __call__(
        self, implementation: classmethod[_Owner, _P, _R], /
    ) -> Alternatives[_NoReceiver, _P, _R, _P]: ...
    @overload
    def __call__(
        self, implementation: staticmethod[_P, _R], /
    ) -> Alternatives[_NoReceiver, _P, _R, _P]: ...
    @overload
    def __call__(
        self, implementation: _FunctionLike[_S, _P, _Q, _R], /
    ) -> Alternatives[_S, _P, _R, _Q]: ...
    @overload
    def __call__(
        self, implementation: Callable[_Q, _R], /
    ) -> Alternatives[_NoReceiver, _Q, _R, _Q]: ...

class AlternativeError(Exception):
    """Base class for all alternative errors."""

class AddTooLateError(AlternativeError):
    """Cannot add implementations after the alternatives have been invoked."""

class MultipleDefaultsError(AlternativeError):
    """Cannot set the default implementation more than once."""

class CrossAlternativesImplementationError(AlternativeError):
    """Cannot add an Implementation object that belongs to a different Alternatives set."""

class _CallableMetadata:
    """Describe the standard metadata preserved on callable wrappers."""

    __wrapped__: object
    __name__: str
    __qualname__: str
    __module__: str
    __doc__: str | None
    __annotations__: dict[str, object]
    def __getattribute__(self, name: str) -> object: ...

@type_check_only
class _PytestDecorators:
    """Preserve test function types for both parametrization APIs."""
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

class _BoundAlternatives(_CallableMetadata, _PytestDecorators, Generic[_S, _P, _R, _Q]):
    __match_args__ = ("alternatives", "instance", "owner")
    alternatives: Alternatives[_S, _P, _R, _Q]
    instance: object | None
    owner: type[object] | None
    if sys.version_info >= (3, 13):
        def __replace__(
            self, /, **changes: object
        ) -> _BoundAlternatives[_S, _P, _R, _Q]: ...
    def __init__(
        self,
        alternatives: Alternatives[_S, _P, _R, _Q],
        instance: object | None,
        owner: type[object] | None,
    ) -> None: ...
    def __post_init__(self) -> None: ...
    @overload
    def __call__(self: _BoundAlternatives[_S, [], _R, _Q], /) -> _R: ...
    @overload
    def __call__(self: _BoundAlternatives[_S, [_A1], _R, _Q], arg1: _A1, /) -> _R: ...
    @overload
    def __call__(
        self: _BoundAlternatives[_S, [_A1, _A2], _R, _Q], arg1: _A1, arg2: _A2, /
    ) -> _R: ...
    @overload
    def __call__(
        self: _BoundAlternatives[_S, [_A1, _A2, _A3], _R, _Q],
        arg1: _A1,
        arg2: _A2,
        arg3: _A3,
        /,
    ) -> _R: ...
    @overload
    def __call__(
        self: _BoundAlternatives[_S, [_A1, _A2, _A3, _A4], _R, _Q],
        arg1: _A1,
        arg2: _A2,
        arg3: _A3,
        arg4: _A4,
        /,
    ) -> _R: ...
    @overload
    def __call__(
        self: _BoundAlternatives[_S, [_A1, _A2, _A3, _A4, _A5], _R, _Q],
        arg1: _A1,
        arg2: _A2,
        arg3: _A3,
        arg4: _A4,
        arg5: _A5,
        /,
    ) -> _R: ...
    @overload
    def __call__(self, /, *args: _P.args, **kwargs: _P.kwargs) -> _R: ...
    @overload
    def add(
        self: _BoundAlternatives[_NoReceiver, _P, _R, _P],
        implementation: classmethod[_Owner, _P, _R]
        | staticmethod[_P, _R]
        | Callable[_P, _R],
        *,
        default: bool = False,
    ) -> Implementation[_NoReceiver, _P, _R, _P]: ...
    @overload
    def add(
        self,
        implementation: _RegistrationInput[_S, _P, _R, _Q],
        *,
        default: bool = False,
    ) -> Implementation[_S, _P, _R, _Q]: ...
    @overload
    def add(self, *, default: bool = False) -> _AddDecorator[_S, _P, _R, _Q]: ...
    @property
    def implementations(self) -> tuple[Implementation[_S, _P, _R, _Q], ...]: ...
    @property
    def reference(self) -> Implementation[_S, _P, _R, _Q]: ...
    @property
    def callable(self) -> Callable[_Q, _R] | _TypedDescriptor[_P, _R]: ...
    def measure(
        self,
        /,
        operator: Callable[[_R], _M],
        *args: _P.args,
        **kwargs: _P.kwargs,
    ) -> dict[Implementation[_S, _P, _R, _Q], _M]: ...

class _BoundImplementation(_CallableMetadata, Generic[_S, _P, _R, _Q]):
    __match_args__ = ("implementation", "instance", "owner")
    implementation: Implementation[_S, _P, _R, _Q]
    instance: object | None
    owner: type[object] | None
    if sys.version_info >= (3, 13):
        def __replace__(
            self, /, **changes: object
        ) -> _BoundImplementation[_S, _P, _R, _Q]: ...
    def __init__(
        self,
        implementation: Implementation[_S, _P, _R, _Q],
        instance: object | None,
        owner: type[object] | None,
    ) -> None: ...
    def __post_init__(self) -> None: ...
    def __call__(self, /, *args: _P.args, **kwargs: _P.kwargs) -> _R: ...
    @overload
    def add(
        self: _BoundImplementation[_NoReceiver, _P, _R, _P],
        implementation: classmethod[_Owner, _P, _R]
        | staticmethod[_P, _R]
        | Callable[_P, _R],
        *,
        default: bool = False,
    ) -> Implementation[_NoReceiver, _P, _R, _P]: ...
    @overload
    def add(
        self,
        implementation: _RegistrationInput[_S, _P, _R, _Q],
        *,
        default: bool = False,
    ) -> Implementation[_S, _P, _R, _Q]: ...
    @overload
    def add(self, *, default: bool = False) -> _AddDecorator[_S, _P, _R, _Q]: ...
    @property
    def alternatives(self) -> Alternatives[_S, _P, _R, _Q]: ...

class Alternatives(_CallableMetadata, _PytestDecorators, Generic[_S, _P, _R, _Q]):
    _reference: Implementation[_S, _P, _R, _Q]
    _default: Implementation[_S, _P, _R, _Q] | None
    _debug_default: str | None
    _callable: _ImplementationSource[_P, _R] | None
    _implementations: list[Implementation[_S, _P, _R, _Q]]
    _implementations_used: bool
    _debug_implementations_used: str | None

    def __init__(
        self,
        implementation: _ImplementationSource[_P, _R],
        *,
        default: bool = False,
    ) -> None: ...
    @overload
    def add(
        self: Alternatives[_NoReceiver, _P, _R, _P],
        implementation: classmethod[_Owner, _P, _R]
        | staticmethod[_P, _R]
        | Callable[_P, _R],
        *,
        default: bool = False,
    ) -> Implementation[_NoReceiver, _P, _R, _P]: ...
    @overload
    def add(
        self,
        implementation: _RegistrationInput[_S, _P, _R, _Q],
        *,
        default: bool = False,
    ) -> Implementation[_S, _P, _R, _Q]: ...
    @overload
    def add(self, *, default: bool = False) -> _AddDecorator[_S, _P, _R, _Q]: ...
    @property
    def reference(self) -> Implementation[_S, _P, _R, _Q]: ...
    @property
    def callable(self) -> Callable[_Q, _R] | _TypedDescriptor[_P, _R]: ...
    @property
    def implementations(self) -> tuple[Implementation[_S, _P, _R, _Q], ...]: ...
    @overload
    def __call__(self: Alternatives[_S, _P, _R, []], /) -> _R: ...
    @overload
    def __call__(self: Alternatives[_S, _P, _R, [_A1]], arg1: _A1, /) -> _R: ...
    @overload
    def __call__(
        self: Alternatives[_S, _P, _R, [_A1, _A2]], arg1: _A1, arg2: _A2, /
    ) -> _R: ...
    @overload
    def __call__(
        self: Alternatives[_S, _P, _R, [_A1, _A2, _A3]],
        arg1: _A1,
        arg2: _A2,
        arg3: _A3,
        /,
    ) -> _R: ...
    @overload
    def __call__(
        self: Alternatives[_S, _P, _R, [_A1, _A2, _A3, _A4]],
        arg1: _A1,
        arg2: _A2,
        arg3: _A3,
        arg4: _A4,
        /,
    ) -> _R: ...
    @overload
    def __call__(
        self: Alternatives[_S, _P, _R, [_A1, _A2, _A3, _A4, _A5]],
        arg1: _A1,
        arg2: _A2,
        arg3: _A3,
        arg4: _A4,
        arg5: _A5,
        /,
    ) -> _R: ...
    @overload
    def __call__(self, /, *args: _Q.args, **kwargs: _Q.kwargs) -> _R: ...
    @overload
    def __get__(
        self: Alternatives[type[_T], _P, _R, _Q], instance: None, owner: type[_T]
    ) -> _BoundAlternatives[type[_T], _P, _R, _Q]: ...
    @overload
    def __get__(
        self: Alternatives[type[_T], _P, _R, _Q],
        instance: _T,
        owner: type[_T] | None = None,
    ) -> _BoundAlternatives[type[_T], _P, _R, _Q]: ...
    @overload
    def __get__(
        self, instance: None, owner: type[object] | None = None
    ) -> Alternatives[_S, _P, _R, _Q]: ...
    @overload
    def __get__(
        self: Alternatives[_NoReceiver, _P, _R, _P],
        instance: object,
        owner: type[object] | None = None,
    ) -> _BoundAlternatives[_NoReceiver, _P, _R, _P]: ...
    @overload
    def __get__(
        self, instance: _S, owner: type[object] | None = None
    ) -> _BoundAlternatives[_S, _P, _R, _Q]: ...
    @overload
    def __get__(
        self, instance: object, owner: type[object] | None = None
    ) -> Alternatives[_S, _P, _R, _Q]: ...
    def _binds_on_class_access(self) -> bool: ...
    def measure(
        self,
        /,
        operator: Callable[[_R], _M],
        *args: _Q.args,
        **kwargs: _Q.kwargs,
    ) -> dict[Implementation[_S, _P, _R, _Q], _M]: ...

class Implementation(_CallableMetadata, Generic[_S, _P, _R, _Q]):
    __match_args__ = ("alternatives", "implementation", "label")
    alternatives: Alternatives[_S, _P, _R, _Q]
    implementation: _ImplementationSource[_P, _R]
    label: str | None

    if sys.version_info >= (3, 13):
        def __replace__(
            self, /, **changes: object
        ) -> Implementation[_S, _P, _R, _Q]: ...
    def __init__(
        self,
        alternatives: Alternatives[_S, _P, _R, _Q],
        implementation: _ImplementationSource[_P, _R],
        label: str | None = None,
    ) -> None: ...
    def __post_init__(self) -> None: ...
    def __hash__(self) -> int: ...
    def __call__(self, /, *args: _Q.args, **kwargs: _Q.kwargs) -> _R: ...
    @overload
    def __get__(
        self: Implementation[type[_T], _P, _R, _Q],
        instance: None,
        owner: type[_T],
    ) -> _BoundImplementation[type[_T], _P, _R, _Q]: ...
    @overload
    def __get__(
        self: Implementation[type[_T], _P, _R, _Q],
        instance: _T,
        owner: type[_T] | None = None,
    ) -> _BoundImplementation[type[_T], _P, _R, _Q]: ...
    @overload
    def __get__(
        self, instance: None, owner: type[object] | None = None
    ) -> Implementation[_S, _P, _R, _Q]: ...
    @overload
    def __get__(
        self: Implementation[_NoReceiver, _P, _R, _P],
        instance: object,
        owner: type[object] | None = None,
    ) -> _BoundImplementation[_NoReceiver, _P, _R, _P]: ...
    @overload
    def __get__(
        self, instance: _S, owner: type[object] | None = None
    ) -> _BoundImplementation[_S, _P, _R, _Q]: ...
    @overload
    def __get__(
        self, instance: object, owner: type[object] | None = None
    ) -> Implementation[_S, _P, _R, _Q]: ...
    @overload
    def add(
        self: Implementation[_NoReceiver, _P, _R, _P],
        implementation: classmethod[_Owner, _P, _R]
        | staticmethod[_P, _R]
        | Callable[_P, _R],
        *,
        default: bool = False,
    ) -> Implementation[_NoReceiver, _P, _R, _P]: ...
    @overload
    def add(
        self,
        implementation: _RegistrationInput[_S, _P, _R, _Q],
        *,
        default: bool = False,
    ) -> Implementation[_S, _P, _R, _Q]: ...
    @overload
    def add(self, *, default: bool = False) -> _AddDecorator[_S, _P, _R, _Q]: ...

@overload
def reference(
    implementation: classmethod[_Owner, _P, _R], *, default: bool = False
) -> Alternatives[_NoReceiver, _P, _R, _P]: ...
@overload
def reference(
    implementation: staticmethod[_P, _R], *, default: bool = False
) -> Alternatives[_NoReceiver, _P, _R, _P]: ...
@overload
def reference(
    implementation: _FunctionLike[_S, _P, _Q, _R], *, default: bool = False
) -> Alternatives[_S, _P, _R, _Q]: ...
@overload
def reference(
    implementation: Callable[_Q, _R], *, default: bool = False
) -> Alternatives[_NoReceiver, _Q, _R, _Q]: ...
@overload
def reference(*, default: bool = False) -> _ReferenceDecorator: ...
def _get_caller_path() -> str | None: ...
