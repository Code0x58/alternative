"""Execute typing examples with their original call signatures."""

import runpy
from pathlib import Path

import pytest


@pytest.mark.parametrize("probe", ["type_probes.py", "model_probes.py"])
def test_typing_examples_execute_with_their_original_call_shapes(probe: str) -> None:
    """Keyword, defaulted, variadic, and descriptor calls work at runtime too."""
    runpy.run_path(str(Path(__file__).parent / "typing_tests" / probe))
