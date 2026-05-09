from __future__ import annotations

import dataclasses
import inspect
import os
from functools import wraps, lru_cache
from typing import Callable
from typing import cast, overload


DEBUG = os.environ.get("ALTERNATIVE_DEBUG", "0").lower() in (
    "1",
    "yes",
    "y",
    "true",
    "t",
)


__all__ = [
    "reference",
    "Alternatives",
    "Implementation",
    "AlternativeError",
    "AddTooLateError",
    "MultipleDefaultsError",
    "CrossAlternativesImplementationError",
]


class _UNDEFINED: ...


_UNDEFINED_VALUE = _UNDEFINED()

type ImplementationSig[**P, R] = Callable[P, R] | Implementation[P, R]
type AlternativesWrapper[**P, R] = Callable[[ImplementationSig], Alternatives[P, R]]
type ImplementationWrapper[**P, R] = Callable[[ImplementationSig], Implementation[P, R]]


class AlternativeError(Exception):
    """Base class for all alternative errors."""


class AddTooLateError(AlternativeError):
    """Cannot add implementations after the alternatives have been invoked."""


class MultipleDefaultsError(AlternativeError):
    """Cannot set the default implementation more than once."""


class CrossAlternativesImplementationError(AlternativeError):
    """Cannot add an Implementation object that belongs to a different Alternatives set."""


def _get_caller_path() -> str | None:
    """
    Return 'module.QualName (file.py:line)' pointing to the line
    that invoked the caller of this function.
    Falls back to '<unknown module>.<unknown> (<unknown location>)'
    if there is no two-up Python frame (e.g. called directly from C embedding).
    """
    frame = inspect.currentframe()
    # Walk back two frames: 0=this, 1=caller, 2=caller of caller
    if not frame or not frame.f_back:
        caller = None  # no two-up frame
    else:
        caller = frame.f_back.f_back

    # walk though any frames that are in the current file as they will not be helpful
    while caller is None or caller.f_code.co_filename == __file__:
        # a bit of a jiggly approach of handling caller being None to make type checking easier and help coverage
        if caller:
            caller = caller.f_back
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


class Alternatives[**P, R]:
    def __init__(self, implementation: Callable[P, R], *, default: bool = False):
        imp = Implementation(self, implementation, label=_maybe_get_caller_path())
        self.reference = imp
        # tracks the active implementation
        self._default: Implementation[P, R] | None = None
        self._debug_default: str | None = None
        self._invoked = False
        self._debug_invoked_site: str | None = None
        # tracks the use of the set should be
        self._enumerated = False
        self._debug_invoked_site: str | None = None

        self._callable: Callable[P, R] | None = None
        self._debug_callable_used: str | None = None

        # beware the order of this depends on the sequence of imports, so may vary between entrypoints
        self._implementations: list[Implementation[P, R]] = []
        self._implementations_used: bool = False
        """indicates if the list of implementations has been used though the external API"""
        self._debug_implementations_used: str | None = None
        self.add(imp, default=default)

    @overload
    def add(
        self, implementation: _UNDEFINED = _UNDEFINED_VALUE, *, default: bool = False
    ) -> ImplementationWrapper[P, R]: ...
    @overload
    def add(
        self, implementation: ImplementationSig[P, R], *, default: bool = False
    ) -> Implementation[P, R]: ...

    def add(
        self,
        implementation=_UNDEFINED_VALUE,
        *,
        default=False,
    ) -> Implementation[P, R] | ImplementationWrapper[P, R]:
        if self._implementations_used:
            # avoid surprises from implementation changes after selection/inspection
            if DEBUG:
                msg = f"added implementation after first invocation at {self._debug_implementations_used}"
            else:
                msg = None
            raise AddTooLateError(msg)

        if isinstance(implementation, _UNDEFINED):

            def wrapper(
                implementation: ImplementationSig[P, R],
            ) -> Implementation[P, R]:
                return self.add(implementation, default=default)

            return cast(ImplementationWrapper[P, R], wrapper)

        label = _maybe_get_caller_path()
        if not isinstance(implementation, Implementation):
            imp = Implementation(self, implementation, label=label)
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
    def callable(self) -> Callable[P, R]:
        """Return the active implementation.

        Setting the default implementation is disabled after this is accessed."""
        if self._callable is None:
            # finalise the callable
            if self._default:
                self._callable = self._default.implementation
            else:
                self._callable = self.reference
            self._debug_callable_used = _maybe_get_caller_path()
            self.__call__ = self._callable
            # access the list of implementations to freeze them
            assert self.implementations
        return self._callable

    @property
    def implementations(self) -> list[Implementation[P, R]]:
        if not self._implementations_used:
            self._implementations_used = True
            self._debug_implementations_used = _maybe_get_caller_path()
        return self._implementations

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        # this method will only be called at most once as self.callable overwrites self.__call__
        return self.callable(*args, **kwargs)

    def measure[M](
        self, /, operator: Callable[[R], M], *args: P.args, **kwargs: P.kwargs
    ) -> dict[Implementation[P, R], M]:
        """Invoke each implementation with the given parameters, then evaluate their results with the operator.

        This is useful when comparing implementations that have different results, which can be compared by some cost.
        For example, this can be used to compare the complexity of quantum circuits that implement the same function.

        The results are sorted by the operator's result if the result is sortable (i.e. does not raise TypeError when
        __lt__(a,b) is called); otherwise they are returned in the order of the implementations.
        """
        result = {
            i: operator(i.implementation(*args, **kwargs)) for i in self.implementations
        }
        try:
            # try to sort the dictionary by the measurements
            return dict(sorted(result.items(), key=lambda x: x[1]))
        except TypeError:
            return result

    @overload
    def pytest_parametrize(
        self,
        test: _UNDEFINED = _UNDEFINED_VALUE,
        *,
        only_default: bool = False,
    ): ...
    @overload
    def pytest_parametrize(
        self,
        test: Callable,
        *,
        only_default: bool = False,
    ): ...
    def pytest_parametrize(
        self,
        test=_UNDEFINED_VALUE,
        *,
        only_default: bool = False,
    ):
        """Decorator to parametrise a test function with implementations - always includes the reference implementation.

        :param test: Test function to wrap - this is elided if using the decorator syntax.
        :parameter only_default: Only include the reference and default implementations. If False, include all implementations.
        """
        import pytest

        if isinstance(test, _UNDEFINED):

            def inner(f: Callable):
                return self.pytest_parametrize(f, only_default=only_default)

            return inner

        implementations = self._select_parametrize_implementations(
            only_default=only_default
        )

        @pytest.mark.parametrize("implementation", implementations)
        @wraps(test)
        def inner(*args, **kwargs):
            return test(*args, **kwargs)

        return inner

    @overload
    def pytest_parametrize_pairs(
        self,
        test: _UNDEFINED = _UNDEFINED_VALUE,
        *,
        n_cache: int | None = 0,
        double_reference: bool = False,
        only_default: bool = False,
    ): ...
    @overload
    def pytest_parametrize_pairs(
        self,
        test: Callable,
        *,
        n_cache: int | None = 0,
        double_reference: bool = False,
        only_default: bool = False,
    ): ...

    def pytest_parametrize_pairs(
        self,
        test=_UNDEFINED_VALUE,
        *,
        n_cache=0,
        double_reference=False,
        only_default=False,
    ):
        """Decorator to parametrise a test function with the reference and alternative implementations.

        :parameter test: Inner pytest function to parameterise with reference and alternative implementations - this is elided if using the decorator syntax.
        :parameter n_cache: Passed to lru_cache which wraps the reference implementation. Set to non-0 values for
            it to actually cache.
        :parameter double_reference: If True, the reference implementation will be included in the implementations. This
            can be used for sanity-checking equivalence tests.
        :parameter only_default: If True, only the default implementation will be used as the other implementation. If
            double_reference is True, the reference implementation will be included as well.
        """
        import pytest

        if isinstance(test, _UNDEFINED):

            def inner(f: Callable):
                return self.pytest_parametrize_pairs(
                    f,
                    n_cache=n_cache,
                    double_reference=double_reference,
                    only_default=only_default,
                )

            return inner

        reference_implementation = lru_cache(maxsize=n_cache)(
            self.reference.implementation
        )

        implementations = self._select_parametrize_pairs(
            reference_implementation=reference_implementation,
            only_default=only_default,
            double_reference=double_reference,
        )

        @pytest.mark.parametrize("reference", [reference_implementation])
        @pytest.mark.parametrize("implementation", implementations)
        @wraps(test)
        def inner(*args, **kwargs):
            return test(*args, **kwargs)

        return inner

    def _select_parametrize_implementations(
        self, *, only_default: bool
    ) -> list[Callable[P, R]]:
        """Return implementation callables used for ``pytest_parametrize``."""
        if only_default:
            reference_implementation = self.reference.implementation
            default_implementation = self.callable
            implementations = [reference_implementation]
            if default_implementation is not reference_implementation:
                implementations.append(default_implementation)
            return implementations
        return [i.implementation for i in self.implementations]

    def _select_parametrize_pairs(
        self,
        *,
        reference_implementation: Callable[P, R],
        only_default: bool,
        double_reference: bool,
    ) -> list[Callable[P, R]]:
        """Return implementation callables used for ``pytest_parametrize_pairs``."""
        # use underlying functions so pytest can generate readable IDs.
        if only_default:
            implementations = [self.callable]
            if double_reference and self.callable is not self.reference.implementation:
                implementations[:0] = [reference_implementation]
            return implementations

        implementations = [i.implementation for i in self.implementations[1:]]
        if double_reference:
            implementations[:0] = [reference_implementation]
        return implementations


@dataclasses.dataclass(unsafe_hash=True)
class Implementation[**P, R]:
    alternatives: Alternatives[P, R]
    implementation: Callable[P, R]
    label: str | None = None

    def __post_init__(self):
        if self.label is None:
            self.label = _maybe_get_caller_path()

    def __repr__(self) -> str:
        implementation_name = getattr(
            self.implementation, "__qualname__", repr(self.implementation)
        )
        if self.label:
            return f"Implementation({implementation_name}, label={self.label!r})"
        return f"Implementation({implementation_name})"

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        self.__call__ = self.implementation
        return self.__call__(*args, **kwargs)

    @overload
    def add(
        self, implementation: _UNDEFINED = _UNDEFINED_VALUE, *, default: bool = False
    ) -> ImplementationWrapper[P, R]: ...
    @overload
    def add(
        self, implementation: ImplementationSig[P, R], *, default: bool = False
    ) -> Implementation[P, R]: ...

    def add(
        self, implementation=_UNDEFINED_VALUE, *, default=False
    ) -> Implementation[P, R] | ImplementationWrapper[P, R]:
        """Add an alternative implementation."""
        return self.alternatives.add(implementation, default=default)


@overload
def reference[**P, R](
    implementation: _UNDEFINED = _UNDEFINED_VALUE, *, default: bool = False
) -> AlternativesWrapper[P, R]: ...


@overload
def reference[**P, R](
    implementation: ImplementationSig[P, R], *, default: bool = False
) -> Alternatives[P, R]: ...


def reference[**P, R](
    implementation=_UNDEFINED_VALUE, *, default=False
) -> Alternatives[P, R] | AlternativesWrapper[P, R]:
    if isinstance(implementation, _UNDEFINED):

        def inner(f: Callable[P, R]) -> Alternatives[P, R]:
            """Add the reference implementation to the alternatives"""
            return Alternatives(f, default=default)

        return cast(AlternativesWrapper[P, R], inner)
    else:
        return Alternatives(implementation, default=default)
