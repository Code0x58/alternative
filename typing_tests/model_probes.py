"""Keep generic parameter order and shared decorator contracts explicit."""

from typing_extensions import assert_type

import alternative


@alternative.reference
def repeat(count: int, label: str, /) -> str:
    """Return a repeated label."""
    return count * label


@repeat.add
def repeat_candidate(count: int, label: str, /) -> str:
    """Supply another implementation with the same signature."""
    return label * count


explicit_set: alternative.Alternatives[int, [str], str, [int, str]] = repeat
explicit_candidate: alternative.Implementation[int, [str], str, [int, str]] = (
    repeat_candidate
)
assert_type(explicit_set(2, "a"), str)
assert_type(explicit_candidate(2, "a"), str)


@repeat.pytest_parametrize
def check_one(implementation: object, *, label: str = "a") -> str:
    """Preserve a directly decorated test function's signature."""
    return label


@repeat.pytest_parametrize(only_default=True)
def check_one_factory(implementation: object, *, label: str = "a") -> str:
    """Preserve the parametrization factory's decorated function signature."""
    return label


@repeat.pytest_parametrize_pairs
def check_pair(reference: object, implementation: object, *, label: str = "a") -> str:
    """Preserve a pairwise test function's signature."""
    return label


@repeat.pytest_parametrize_pairs(n_cache=None, double_reference=True)
def check_pair_factory(
    reference: object, implementation: object, *, label: str = "a"
) -> str:
    """Preserve the pairwise decorator factory's function signature."""
    return label


assert_type(check_one(object(), label="a"), str)
assert_type(check_one_factory(object(), label="a"), str)
assert_type(check_pair(object(), object(), label="a"), str)
assert_type(check_pair_factory(object(), object(), label="a"), str)


class Methods:
    """Expose the same decorators through a receiver-bound view."""

    @alternative.reference
    def repeat(self, count: int, label: str) -> str:
        """Repeat a label through an instance method."""
        return count * label


bound = Methods().repeat
assert_type(next(iter(bound.measure(len, count=2, label="a").values())), int)
assert_type(next(iter(Methods.repeat.measure(len, Methods(), 2, "a").values())), int)


@bound.pytest_parametrize
def check_bound_one(implementation: object, *, label: str = "a") -> str:
    """Keep the directly decorated bound-view test signature."""
    return label


@bound.pytest_parametrize(only_default=True)
def check_bound_one_factory(implementation: object, *, label: str = "a") -> str:
    """Keep the bound-view decorator factory's test signature."""
    return label


@bound.pytest_parametrize_pairs
def check_bound_pair(
    reference: object, implementation: object, *, label: str = "a"
) -> str:
    """Keep the directly decorated bound-view pair signature."""
    return label


@bound.pytest_parametrize_pairs(n_cache=None, double_reference=True)
def check_bound_pair_factory(
    reference: object, implementation: object, *, label: str = "a"
) -> str:
    """Keep the bound-view pair decorator factory's test signature."""
    return label


assert_type(check_bound_one(object(), label="a"), str)
assert_type(check_bound_one_factory(object(), label="a"), str)
assert_type(check_bound_pair(object(), object(), label="a"), str)
assert_type(check_bound_pair_factory(object(), object(), label="a"), str)


@alternative.reference
def sum_six(
    first: int, second: int, third: int, fourth: int, fifth: int, sixth: int
) -> int:
    """Preserve signatures beyond the positional IDE workaround's arity."""
    return first + second + third + fourth + fifth + sixth


assert_type(sum_six(1, 2, 3, 4, 5, 6), int)
assert_type(sum_six(first=1, second=2, third=3, fourth=4, fifth=5, sixth=6), int)


@alternative.reference
def constant() -> str:
    """Keep a signature without a receiver or arguments."""
    return "a"


@alternative.reference
def only_keywords(*, label: str) -> str:
    """Keep a required keyword-only signature."""
    return label


assert_type(constant(), str)
assert_type(only_keywords(label="a"), str)
