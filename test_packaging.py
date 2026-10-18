import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest


@pytest.fixture(scope="module")
def wheel_path(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Build the wheel used by archive and installed-consumer checks."""
    directory = tmp_path_factory.mktemp("wheel")
    subprocess.run(
        [
            sys.executable,
            "-m",
            "build",
            "--wheel",
            "--no-isolation",
            "--outdir",
            str(directory),
        ],
        check=True,
        cwd=Path(__file__).resolve().parent,
    )

    wheels = sorted(directory.glob("alternative-*.whl"))
    assert len(wheels) == 1
    return wheels[0]


def test_wheel_includes_stub(wheel_path: Path) -> None:
    """The built package ships its implementation, stub, and PEP 561 marker."""
    with zipfile.ZipFile(wheel_path) as wheel:
        names = set(wheel.namelist())

    assert "alternative/__init__.py" in names
    assert "alternative/__init__.pyi" in names
    assert "alternative/py.typed" in names


@pytest.fixture(scope="module")
def installed_consumer(
    wheel_path: Path, tmp_path_factory: pytest.TempPathFactory
) -> tuple[Path, Path]:
    """Install the wheel without dependencies and copy probes outside the checkout."""
    directory = tmp_path_factory.mktemp("installed-consumer")
    environment = directory / "environment"
    python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    subprocess.run(
        ["uv", "venv", "--python", sys.executable, str(environment)], check=True
    )
    subprocess.run(
        ["uv", "pip", "install", "--python", str(python), "--no-deps", str(wheel_path)],
        check=True,
    )
    probe = directory / "consumer.py"
    shutil.copyfile(
        Path(__file__).parent / "typing_tests" / "callable_probes.py", probe
    )
    return python, probe


@pytest.mark.parametrize("checker", ["mypy", "pyright", "pyrefly"])
def test_installed_wheel_preserves_typing(
    installed_consumer: tuple[Path, Path], checker: str
) -> None:
    """Type check an external consumer against only the installed distribution."""
    python, probe = installed_consumer
    if checker == "mypy":
        command = [
            sys.executable,
            "-m",
            "mypy",
            "--no-incremental",
            "--python-executable",
            str(python),
        ]
    elif checker == "pyright":
        command = [sys.executable, "-m", "pyright", "--pythonpath", str(python)]
    else:
        executable = shutil.which("pyrefly")
        assert executable is not None
        command = [executable, "check", "--python-interpreter-path", str(python)]
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    environment.pop("MYPYPATH", None)
    subprocess.run(
        [*command, str(probe)], cwd=probe.parent, env=environment, check=True
    )
