"""Check that headless inspection cannot silently skip the typing probes."""

from pathlib import Path
import subprocess
import sys

import pytest


@pytest.mark.parametrize(
    ("mode", "status", "message"),
    [
        ("clean", 0, ""),
        ("source_error", 1, "typing_tests/type_probes.py:2: PyAssertTypeInspection"),
        ("missing_reports", 2, "failure controls"),
        ("missing_control", 2, "PyTypeCheckerInspection"),
        ("wrong_file", 2, "failure controls"),
        ("crash", 2, "inspect.sh failed"),
        ("malformed_report", 2, "Invalid PyCharm inspection results"),
    ],
)
def test_pycharm_inspection_requires_failure_controls(
    tmp_path: Path, mode: str, status: int, message: str
) -> None:
    """Only complete inspections with clean source probes succeed silently."""
    source = tmp_path / "source"
    package = source / "alternative"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text('"""Inspection fixture package."""\n')
    probe = source / "typing_tests/type_probes.py"
    probe.parent.mkdir()
    probe.write_text("from typing_extensions import assert_type\nassert_type(1, int)\n")
    inspect_sh = tmp_path / "inspect.sh"
    inspect_sh.write_text(
        f"#!{sys.executable}\n"
        + f"MODE = {mode!r}\n"
        + """\
import os
from pathlib import Path
import sys
import xml.etree.ElementTree as et

project, profile, results = map(Path, sys.argv[1:4])
assert project != Path(sys.argv[0]).parent / "source"
assert (project / "alternative/__init__.py").is_file()
assert (project / ".idea/misc.xml").is_file()
module = et.parse(project / "inspection.iml")
assert module.find(".//content").get("url") == project.as_uri()
assert 'idea.config.path=' in Path(os.environ["PYCHARM_VM_OPTIONS"]).read_text()
assert et.parse(profile).getroot().tag == "profile"
if MODE == "crash":
    sys.exit(1)
results.mkdir()
if MODE == "missing_reports":
    sys.exit(0)
for tool in et.parse(profile).findall("inspection_tool"):
    name = tool.get("class")
    root = et.Element("problems")
    if MODE != "missing_control" or name != "PyTypeCheckerInspection":
        control = et.SubElement(root, "problem")
        filename = "other.py" if MODE == "wrong_file" else "typing_tests/type_probes.py"
        et.SubElement(control, "file").text = "file://$PROJECT_DIR$/" + filename
        et.SubElement(control, "line").text = "5"
        et.SubElement(control, "description").text = "Deliberate failure control"
    if MODE == "source_error" and name == "PyAssertTypeInspection":
        problem = et.SubElement(root, "problem")
        et.SubElement(problem, "file").text = "file://$PROJECT_DIR$/typing_tests/type_probes.py"
        et.SubElement(problem, "line").text = "2"
        et.SubElement(problem, "description").text = "Expected type str, got int"
    report = results / (name + ".xml")
    et.ElementTree(root).write(report)
    if MODE == "malformed_report":
        report.write_text("<problems")
"""
    )
    inspect_sh.chmod(0o755)
    script = Path(__file__).parent / "scripts/pycharm_type_probes.py"
    result = subprocess.run(
        [sys.executable, str(script), str(source), str(inspect_sh)],
        capture_output=True,
        text=True,
    )
    output = result.stdout + result.stderr
    assert result.returncode == status, output
    if message:
        assert message in output
    else:
        assert not output
    assert not (source / ".idea").exists()
    assert probe.read_text().endswith("assert_type(1, int)\n")
