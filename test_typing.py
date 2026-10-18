"""Check that invalid public API calls produce useful type diagnostics."""

import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize("checker", ["mypy", "pyright", "pyrefly"])
@pytest.mark.parametrize("probe_name", ["invalid_calls.py", "invalid_registration.py"])
def test_invalid_typing_examples_are_rejected(
    tmp_path: Path, checker: str, probe_name: str
) -> None:
    """Every marked misuse fails, without errors on valid setup or imports."""
    root = Path(__file__).resolve().parent
    source = (root / "typing_tests" / (probe_name + ".txt")).read_text()
    probe = tmp_path / probe_name
    probe.write_text(source)
    expected_lines = {
        index
        for index, line in enumerate(source.splitlines(), start=1)
        if "# error" in line
    }
    assert expected_lines
    if checker == "mypy":
        command = [sys.executable, "-m", "mypy", "--no-incremental"]
    elif checker == "pyright":
        command = [sys.executable, "-m", "pyright", "--pythonpath", sys.executable]
    else:
        executable = shutil.which("pyrefly")
        assert executable is not None
        command = [
            executable,
            "check",
            "--config",
            str(root / "pyproject.toml"),
            "--python-interpreter-path",
            sys.executable,
        ]
    result = subprocess.run(
        [*command, str(probe)], check=False, cwd=root, capture_output=True, text=True
    )
    output = result.stdout + result.stderr
    assert result.returncode == 1, output
    diagnosed_lines = {
        int(line) for line in re.findall(re.escape(str(probe)) + r":(\d+):", output)
    }
    assert diagnosed_lines == expected_lines, output
