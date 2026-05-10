from __future__ import annotations

from sybil import Sybil
from sybil.parsers.rest import PythonCodeBlockParser

pytest_collect_file = Sybil(
    parsers=[PythonCodeBlockParser()],
    patterns=["*.rst"],
).pytest()
