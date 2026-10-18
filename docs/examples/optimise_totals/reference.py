"""Keep a straightforward implementation as a correctness oracle."""

from collections.abc import Iterable

import alternative


@alternative.reference
def total(values: Iterable[int]) -> int:
    """Sum integers, including empty inputs and arbitrarily large values."""
    result = 0
    for value in values:
        result += value
    return result
