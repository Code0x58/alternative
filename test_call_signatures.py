"""Execute typing examples with their original call signatures."""

import runpy
from pathlib import Path


def test_typing_examples_execute_with_their_original_call_shapes() -> None:
    """Keyword, defaulted, variadic, and descriptor calls work at runtime too."""
    runpy.run_path(str(Path(__file__).parent / "typing_tests" / "type_probes.py"))
