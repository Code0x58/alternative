"""Check that copying a reference does not connect alternatives sets."""

import alternative


def test_copy_uses_reference_instead_of_source_default() -> None:
    """Copying a set chooses its reference even when it has another default."""
    source = alternative.reference(lambda: 1)
    source.add(lambda: 2, default=True)
    target = alternative.reference(lambda: 10)
    copied = target.add(source, default=True)
    assert copied.implementation is source.reference.implementation
    assert copied.alternatives is target
    assert copied() == target() == 1
    assert source() == 2


def test_copy_does_not_freeze_or_follow_source_selection() -> None:
    """Invoking a copy leaves the source free to register its own default."""
    source = alternative.reference(lambda: 1)
    target = alternative.reference(lambda: 10)
    copied = target.add(source)
    assert copied() == 1
    source.add(lambda: 2, default=True)
    assert source() == 2
    assert copied() == 1
