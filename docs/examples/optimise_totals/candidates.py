"""Select a candidate while registration is still open."""

from collections.abc import Iterable

from .reference import total


@total.add(default=True)
def total_builtin(values: Iterable[int]) -> int:
    """Use Python's integer sum with the same public contract."""
    return sum(values)
