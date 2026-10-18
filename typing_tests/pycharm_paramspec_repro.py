"""Reproduce PyCharm's ParamSpec callback inference failure without alternative."""

from typing import Callable, ParamSpec, Protocol, TypeVar

from typing_extensions import assert_type

P = ParamSpec("P")
R = TypeVar("R")
R_co = TypeVar("R_co", covariant=True)


class ForwardCall(Protocol[P, R_co]):
    """Preserve the callable signature in a callback protocol."""

    def __call__(self, /, *args: P.args, **kwargs: P.kwargs) -> R_co: ...


def preserve(function: Callable[P, R]) -> ForwardCall[P, R]:
    """Return the original function with its declared callback type."""
    return function


@preserve
def repeat(count: int = 2, *, label: str = "a") -> str:
    """Repeat a label a specified number of times."""
    return count * label


assert_type(repeat(count=2), str)
