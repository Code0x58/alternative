"""Rebuild the sdist and smoke-test each wheel in an isolated installation."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from packaging.version import Version

SMOKE_TEST = '''
from importlib import metadata
from pathlib import Path
import sys

import alternative

assert Path(alternative.__file__).resolve().is_relative_to(Path(sys.prefix).resolve())
distribution = metadata.distribution("alternative")
assert distribution.metadata["License-Expression"] == "MIT"
assert distribution.metadata.get_all("License-File")
if sys.argv[1]:
    assert distribution.version == sys.argv[1], distribution.version

@alternative.reference
def total(values: list[int]) -> int:
    """Return the reference result for an installed package."""
    return sum(values)

@total.add(default=True)
def candidate(values: list[int]) -> int:
    """Exercise registration and default dispatch after installation."""
    return sum(values)

assert total([1, 2, 3]) == 6
assert total.reference([1, 2, 3]) == 6
assert candidate([1, 2, 3]) == 6
assert len(total.implementations) == 2
print(f"Validated {distribution.metadata['Name']} {distribution.version}")
'''


def check_wheel(wheel: Path, directory: Path, expected_version: str) -> None:
    """Install one wheel without dependencies and exercise its public API."""
    environment = directory / "environment"
    python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    subprocess.run(
        ["uv", "venv", "--python", sys.executable, str(environment)], check=True
    )
    subprocess.run(
        ["uv", "pip", "install", "--python", str(python), "--no-deps", str(wheel)],
        check=True,
    )
    subprocess.run(
        [str(python), "-I", "-c", SMOKE_TEST, expected_version],
        cwd=directory,
        check=True,
    )


def main() -> None:
    """Validate the wheel and sdist, optionally matching a release tag."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--expected-version")
    arguments = parser.parse_args()
    expected_version = (
        str(Version(arguments.expected_version)) if arguments.expected_version else ""
    )
    if expected_version:
        version = Version(expected_version)
        if version.is_devrelease or version.local:
            parser.error("release tags must not contain development or local versions")

    directory = arguments.directory.resolve()
    wheels = list(directory.glob("*.whl"))
    sdists = list(directory.glob("*.tar.gz"))
    if len(wheels) != 1 or len(sdists) != 1:
        parser.error("expected exactly one wheel and one source distribution")

    with tempfile.TemporaryDirectory(prefix="alternative-distributions-") as temporary:
        scratch = Path(temporary)
        check_wheel(wheels[0], scratch / "wheel", expected_version)
        rebuilt = scratch / "rebuilt"
        subprocess.run(
            [
                "uv",
                "build",
                str(sdists[0]),
                "--wheel",
                "--no-build-isolation",
                "--python",
                sys.executable,
                "--out-dir",
                str(rebuilt),
            ],
            check=True,
        )
        rebuilt_wheels = list(rebuilt.glob("*.whl"))
        if len(rebuilt_wheels) != 1:
            parser.error("the source distribution must build exactly one wheel")
        check_wheel(rebuilt_wheels[0], scratch / "sdist", expected_version)


if __name__ == "__main__":
    main()
