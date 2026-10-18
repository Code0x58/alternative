"""Check that public metadata cannot bypass registration safeguards."""

from dataclasses import FrozenInstanceError

import pytest

import alternative


def test_implementation_snapshot_cannot_extend_registry() -> None:
    """Adding to a snapshot leaves the inspected registry unchanged."""
    wrapped = alternative.reference(lambda: 1)
    snapshot = wrapped.implementations
    extra = alternative.Implementation(wrapped, lambda: 2)
    snapshot += (extra,)
    assert len(snapshot) == 2
    assert len(wrapped.implementations) == 1
    with pytest.raises(alternative.AddTooLateError):
        wrapped.add(extra)


@pytest.mark.parametrize("explicit_default", [False, True])
def test_public_implementations_are_immutable(explicit_default: bool) -> None:
    """Reference and candidate wrappers cannot change after selection."""
    wrapped = alternative.reference(lambda: 1)
    candidate = wrapped.add(lambda: 2, default=explicit_default)
    expected = 2 if explicit_default else 1
    assert wrapped() == expected
    for implementation in (wrapped.reference, candidate):
        for name, value in (
            ("implementation", lambda: 3),
            ("alternatives", alternative.reference(lambda: 4)),
            ("label", "changed"),
        ):
            with pytest.raises(FrozenInstanceError):
                setattr(implementation, name, value)
    with pytest.raises(AttributeError):
        setattr(wrapped, "reference", candidate)
    assert wrapped() == expected


def test_implementation_hash_is_stable() -> None:
    """Measurements keep usable implementation keys after attempted changes."""
    wrapped = alternative.reference(lambda: 1)
    measurements = wrapped.measure(int)
    with pytest.raises(FrozenInstanceError):
        setattr(wrapped.reference, "label", "changed")
    assert measurements[wrapped.implementations[0]] == 1
