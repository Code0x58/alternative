"""Exercise real pytest-asyncio collection and safe reference-cache boundaries."""

import inspect
from collections.abc import AsyncIterator, Iterator

import pytest

import alternative


def call_parameters(decorated):
    """Read the parameters attached dynamically by pytest."""
    return {mark.args[0]: mark.args[1][0] for mark in decorated.pytestmark}


@alternative.reference
async def async_reference(value: int) -> int:
    """Return a value asynchronously."""
    return value


@async_reference.add
async def async_candidate(value: int) -> int:
    """Return the same value asynchronously."""
    return value


@pytest.mark.asyncio
@async_reference.pytest_parametrize
async def test_async_single_implementation(implementation) -> None:
    """The async plugin awaits directly parametrized test bodies."""
    assert await implementation(3) == 3


@async_reference.pytest_parametrize_pairs()
@pytest.mark.asyncio
async def test_async_pair(reference, implementation) -> None:
    """Decorator factories and either marker order preserve asynchronous tests."""
    assert await reference(3) == await implementation(3) == 3
    assert await reference(3) == 3


def test_async_test_metadata_and_marks_are_isolated() -> None:
    """Reusing a test function does not accumulate duplicate parametrizations."""

    async def original(implementation) -> int:
        """Return an awaited result."""
        return await implementation(2)

    first = async_reference.pytest_parametrize(original)
    second = async_reference.pytest_parametrize(original)
    assert inspect.iscoroutinefunction(first)
    assert inspect.iscoroutinefunction(second)
    assert inspect.signature(first) == inspect.signature(original)
    assert not hasattr(original, "pytestmark")


def generator_reference() -> Iterator[int]:
    """Yield one integer."""
    yield 1


async def async_generator_reference() -> AsyncIterator[int]:
    """Yield one integer asynchronously."""
    yield 1


class AsyncCallable:
    """Produce a coroutine through a callable instance."""

    async def __call__(self) -> int:
        """Return an integer asynchronously."""
        return 1


@pytest.mark.parametrize(
    "source",
    [
        async_reference.reference.implementation,
        generator_reference,
        async_generator_reference,
        AsyncCallable(),
    ],
)
@pytest.mark.parametrize("n_cache", [None, 2])
def test_single_use_reference_caching_is_rejected(source, n_cache) -> None:
    """Cache misuse fails during decoration before creating a single-use result."""
    wrapped = alternative.reference(source)

    def placeholder(reference, implementation):
        """Accept a reference and candidate."""

    with pytest.raises(ValueError, match="use n_cache=0"):
        wrapped.pytest_parametrize_pairs(placeholder, n_cache=n_cache)


def test_generator_reference_without_caching_is_reusable() -> None:
    """Disabling caching creates a fresh iterator for each reference call."""
    wrapped = alternative.reference(generator_reference)

    def placeholder(reference, implementation):
        """Consume two independently created generators."""
        assert list(reference()) == list(reference()) == [1]
        assert list(implementation()) == [1]

    decorated = wrapped.pytest_parametrize_pairs(placeholder, only_default=True)
    parameters = call_parameters(decorated)
    decorated(**parameters)
