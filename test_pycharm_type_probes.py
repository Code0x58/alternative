"""Check that headless inspection cannot silently skip the typing probes."""

import json
import subprocess
import sys
from pathlib import Path

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
        ("xfail", 0, ""),
        ("xfail_extra", 1, "Unresolved reference"),
        ("xfail_changed", 1, "changed diagnostic"),
        ("xfail_xpass", 1, "XPASS"),
        ("xfail_partial", 1, "XPASS"),
        ("xfail_duplicate_diagnostic", 1, "Expected type str, got int"),
        ("xfail_removed_probe", 2, "must identify one assertion"),
        ("xfail_duplicate_case", 2, "must identify one assertion"),
        ("xfail_missing_issue", 2, "missing issue"),
        ("xfail_missing_control", 2, "failure controls"),
        ("xfail_invalid_json", 2, "Invalid PyCharm xfail manifest"),
        ("xfail_reformatted", 0, ""),
        ("xfail_show", 0, "XFAIL assert_type(1, int)"),
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
    original = "from typing_extensions import assert_type\nassert_type(1, int)\n"
    if mode == "xfail_reformatted":
        original = (
            "from typing_extensions import assert_type\n\nassert_type(\n1, int\n)\n"
        )
    probe.write_text(original)
    if mode.startswith("xfail"):
        case = {
            "expression": "assert_type(1, int)",
            "gap": "callback-inference",
            "diagnostics": [["PyAssertTypeInspection", "Expected type str, got int"]],
        }
        if mode == "xfail_removed_probe":
            case["expression"] = "assert_type(2, int)"
        if mode == "xfail_partial":
            case["diagnostics"] = [
                ["PyAssertTypeInspection", "Expected type str, got int"],
                ["PyTypeCheckerInspection", "Parameter self unfilled"],
            ]
        manifest = {
            "gaps": {
                "callback-inference": {
                    "issue": "https://youtrack.jetbrains.com/issue/PY-77541"
                }
            },
            "cases": [case] * (2 if mode == "xfail_duplicate_case" else 1),
        }
        if mode == "xfail_missing_issue":
            manifest["gaps"] = {}
        manifest_path = source / "typing_tests/pycharm_xfails.json"
        manifest_path.write_text(
            "{" if mode == "xfail_invalid_json" else json.dumps(manifest)
        )
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
probe_lines = (project / "typing_tests/type_probes.py").read_text().splitlines()
control_line = next(i for i, line in enumerate(probe_lines, 1) if "_pycharm_expected_int: int" in line)
source_line = 4 if MODE == "xfail_reformatted" else 2
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
    if MODE not in {"missing_control", "xfail_missing_control"} or name != "PyTypeCheckerInspection":
        control = et.SubElement(root, "problem")
        filename = "other.py" if MODE == "wrong_file" else "typing_tests/type_probes.py"
        et.SubElement(control, "file").text = "file://$PROJECT_DIR$/" + filename
        et.SubElement(control, "line").text = str(control_line)
        et.SubElement(control, "description").text = "Deliberate failure control"
    if (MODE == "source_error" or MODE.startswith("xfail")) and MODE != "xfail_xpass" and name == "PyAssertTypeInspection":
        for _ in range(2 if MODE == "xfail_duplicate_diagnostic" else 1):
            problem = et.SubElement(root, "problem")
            et.SubElement(problem, "file").text = "file://$PROJECT_DIR$/typing_tests/type_probes.py"
            et.SubElement(problem, "line").text = str(source_line)
            et.SubElement(problem, "description").text = "changed diagnostic" if MODE == "xfail_changed" else "Expected type str, got int"
    if MODE == "xfail_extra" and name == "PyUnresolvedReferencesInspection":
        problem = et.SubElement(root, "problem")
        et.SubElement(problem, "file").text = "file://$PROJECT_DIR$/typing_tests/type_probes.py"
        et.SubElement(problem, "line").text = str(source_line)
        et.SubElement(problem, "description").text = "Unresolved reference"
    report = results / (name + ".xml")
    et.ElementTree(root).write(report)
    if MODE == "malformed_report":
        report.write_text("<problems")
"""
    )
    inspect_sh.chmod(0o755)
    script = Path(__file__).parent / "scripts/pycharm_type_probes.py"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            str(source),
            str(inspect_sh),
            *(["--show-xfails"] if mode == "xfail_show" else []),
        ],
        check=False,
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
    assert probe.read_text() == original
