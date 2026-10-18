"""Check registration safeguards with Python assertions disabled."""

import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize("explicit_default", [False, True])
def test_optimized_invocation_freezes_registration(explicit_default: bool) -> None:
    """Optimized Python rejects additions and defaults after the first call."""
    source = f"""
import alternative

@alternative.reference(default={explicit_default!r})
def reference():
    '''Return the reference value.'''
    return 1

if reference() != 1:
    raise RuntimeError("Unexpected initial result")
for default in (False, True):
    try:
        reference.add(lambda: 2, default=default)
    except alternative.AddTooLateError:
        pass
    else:
        raise RuntimeError("Late registration was accepted")
if reference() != 1:
    raise RuntimeError("The selected implementation changed")
"""
    subprocess.run(
        [sys.executable, "-O", "-c", source],
        cwd=Path(__file__).resolve().parent,
        check=True,
        capture_output=True,
        text=True,
    )
