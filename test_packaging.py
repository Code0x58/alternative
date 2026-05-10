import subprocess
import sys
import zipfile
from pathlib import Path


def test_wheel_includes_stub(tmp_path: Path) -> None:
    """The built wheel ships the top-level stub used by type checkers."""
    subprocess.run(
        [
            sys.executable,
            "-m",
            "build",
            "--wheel",
            "--no-isolation",
            "--outdir",
            str(tmp_path),
        ],
        check=True,
        cwd=Path(__file__).resolve().parent,
    )

    wheels = sorted(tmp_path.glob("alternative-*.whl"))
    assert len(wheels) == 1
    with zipfile.ZipFile(wheels[0]) as wheel:
        names = set(wheel.namelist())

    assert "alternative.py" in names
    assert "alternative.pyi" in names
