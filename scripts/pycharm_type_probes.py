"""Inspect a disposable project and require proof that each inspection ran."""

from __future__ import annotations

import ast
import json
import os
import shutil
import subprocess
import sys
import sysconfig
import tempfile
import xml.etree.ElementTree as et
from dataclasses import dataclass
from pathlib import Path

INSPECTIONS = (
    "PyAssertTypeInspection",
    "PyTypeCheckerInspection",
    "PyUnresolvedReferencesInspection",
    "PyArgumentListInspection",
)
CONTROL = '''

# Appended only to the disposable inspection copy.
assert_type(1, str)
_pycharm_expected_int: int = "inspection control"
_pycharm_missing_inspection_control_name

def _pycharm_requires_argument(value: int) -> None:
    """Exercise argument-list inspection."""

_pycharm_requires_argument()
'''


@dataclass(frozen=True)
class Diagnostic:
    """Keep source locations separate from the diagnostic used for matching."""

    line: int
    inspection: str
    description: str

    def __str__(self) -> str:
        """Render an actionable source diagnostic."""
        return (
            f"typing_tests/type_probes.py:{self.line}: "
            f"{self.inspection}: {self.description}"
        )


@dataclass(frozen=True)
class ExpectedFailure:
    """Identify a reviewed probe and its exact known PyCharm diagnostics."""

    expression: str
    issue: str
    start: int
    end: int
    diagnostics: tuple[tuple[str, str], ...]


def load_expected_failures(source: Path) -> list[ExpectedFailure]:
    """Resolve reviewed expressions to lines, rejecting stale or invalid entries."""
    manifest = source / "typing_tests/pycharm_xfails.json"
    if not manifest.is_file():
        return []
    data = json.loads(manifest.read_text())
    if not isinstance(data, dict):
        raise TypeError("expected an object in pycharm_xfails.json")
    gaps, cases = data.get("gaps"), data.get("cases")
    if not isinstance(gaps, dict) or not isinstance(cases, list):
        raise TypeError("expected gaps and cases in pycharm_xfails.json")
    tree = ast.parse((source / "typing_tests/type_probes.py").read_text())
    assertions: dict[str, list[tuple[int, int]]] = {}
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Name)
            and node.value.func.id == "assert_type"
        ):
            assertions.setdefault(ast.unparse(node.value), []).append(
                (node.lineno, node.end_lineno or node.lineno)
            )
    expected: list[ExpectedFailure] = []
    seen: set[str] = set()
    for case in cases:
        if not isinstance(case, dict):
            raise TypeError("expected an object for each PyCharm xfail")
        expression, gap = case.get("expression"), case.get("gap")
        diagnostics = case.get("diagnostics")
        if not isinstance(expression, str) or not isinstance(gap, str):
            raise TypeError("expected an expression and gap for each PyCharm xfail")
        location = assertions.get(expression, [])
        if len(location) != 1 or expression in seen:
            raise ValueError(f"PyCharm xfail must identify one assertion: {expression}")
        seen.add(expression)
        details = gaps.get(gap)
        if not isinstance(details, dict) or not isinstance(details.get("issue"), str):
            raise TypeError(f"missing issue for PyCharm gap: {gap}")
        issue = details["issue"]
        if not isinstance(diagnostics, list) or not diagnostics:
            raise ValueError(f"missing diagnostics for PyCharm xfail: {expression}")
        messages: list[tuple[str, str]] = []
        for diagnostic in diagnostics:
            if (
                not isinstance(diagnostic, list)
                or len(diagnostic) != 2
                or not all(isinstance(part, str) for part in diagnostic)
                or diagnostic[0] not in INSPECTIONS
            ):
                raise ValueError(f"invalid PyCharm xfail diagnostic: {diagnostic}")
            messages.append((diagnostic[0], diagnostic[1]))
        start, end = location[0]
        expected.append(ExpectedFailure(expression, issue, start, end, tuple(messages)))
    return expected


def apply_expected_failures(
    problems: list[Diagnostic], expected: list[ExpectedFailure], *, show_xfails: bool
) -> list[str]:
    """Accept only exact known failures and report every unexpected pass or error."""
    remaining = list(problems)
    failures: list[str] = []
    for case in expected:
        missing = False
        for inspection, description in case.diagnostics:
            match = next(
                (
                    problem
                    for problem in remaining
                    if case.start <= problem.line <= case.end
                    and problem.inspection == inspection
                    and problem.description == description
                ),
                None,
            )
            if match is None:
                missing = True
                failures.append(
                    f"XPASS typing_tests/type_probes.py:{case.start}: "
                    f"{case.expression}: expected {inspection}: {description} "
                    f"({case.issue}); review this xfail"
                )
            else:
                remaining.remove(match)
        if show_xfails and not missing:
            print(f"XFAIL {case.expression} ({case.issue})")
    return [*(str(problem) for problem in remaining), *failures]


def write_xml(path: Path, root: et.Element) -> None:
    """Write an IDE configuration file without shell or XML interpolation."""
    path.parent.mkdir(parents=True, exist_ok=True)
    et.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)


def prepare_project(source: Path, root: Path, inspect_sh: Path) -> tuple[Path, int]:
    """Copy the probes and source, then configure their SDK and content root."""
    project = root / "project"
    shutil.copytree(
        source / "alternative",
        project / "alternative",
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    probe = project / "typing_tests" / "type_probes.py"
    probe.parent.mkdir()
    text = (source / "typing_tests" / "type_probes.py").read_text()
    probe.write_text(text + CONTROL)

    sdk_name = "Alternative inspection SDK"
    application = et.Element("application")
    component = et.SubElement(application, "component", name="ProjectJdkTable")
    jdk = et.SubElement(component, "jdk", version="2")
    for tag, value in (
        ("name", sdk_name),
        ("type", "Python SDK"),
        ("version", "Python " + sys.version.split()[0]),
        ("homePath", sys.executable),
    ):
        et.SubElement(jdk, tag, value=value)
    roots = et.SubElement(jdk, "roots")
    class_path = et.SubElement(
        et.SubElement(roots, "classPath"), "root", type="composite"
    )
    installation = inspect_sh.resolve().parent.parent
    for path in (
        Path(sysconfig.get_path("stdlib")),
        Path(sysconfig.get_path("stdlib")) / "lib-dynload",
        Path(sysconfig.get_path("purelib")),
        installation / "plugins/python-ce/helpers/typeshed/stdlib",
        installation / "plugins/python/helpers/typeshed/stdlib",
    ):
        if path.is_dir():
            et.SubElement(class_path, "root", url=path.as_uri(), type="simple")
    et.SubElement(et.SubElement(roots, "sourcePath"), "root", type="composite")
    et.SubElement(jdk, "additional", ASSOCIATED_PROJECT_PATH=str(project))
    write_xml(root / "config/options/jdk.table.xml", application)

    settings = et.Element("project", version="4")
    et.SubElement(
        settings,
        "component",
        {
            "name": "ProjectRootManager",
            "version": "2",
            "project-jdk-name": sdk_name,
            "project-jdk-type": "Python SDK",
        },
    )
    write_xml(project / ".idea/misc.xml", settings)
    settings = et.Element("project", version="4")
    modules = et.SubElement(
        et.SubElement(settings, "component", name="ProjectModuleManager"), "modules"
    )
    module_path = project / "inspection.iml"
    et.SubElement(
        modules, "module", fileurl=module_path.as_uri(), filepath=str(module_path)
    )
    write_xml(project / ".idea/modules.xml", settings)
    module = et.Element("module", type="PYTHON_MODULE", version="4")
    component = et.SubElement(module, "component", name="NewModuleRootManager")
    et.SubElement(component, "content", url=project.as_uri())
    et.SubElement(
        component, "orderEntry", type="jdk", jdkName=sdk_name, jdkType="Python SDK"
    )
    et.SubElement(component, "orderEntry", type="sourceFolder", forTests="false")
    write_xml(module_path, module)
    return project, len(text.splitlines())


def collect_problems(
    results: Path, source_lines: int
) -> tuple[list[Diagnostic], list[str]]:
    """Separate source diagnostics from controls and reject incomplete inspections."""
    problems: list[Diagnostic] = []
    missing: list[str] = []
    for inspection in INSPECTIONS:
        control_seen = False
        report = results / (inspection + ".xml")
        if report.is_file():
            for problem in et.parse(report).findall(".//problem"):
                if not problem.findtext("file", "").endswith(
                    "/typing_tests/type_probes.py"
                ):
                    continue
                line = int(problem.findtext("line", "0"))
                if line > source_lines:
                    control_seen = True
                else:
                    description = problem.findtext("description", "")
                    problems.append(Diagnostic(line, inspection, description))
        if not control_seen:
            missing.append(inspection)
    return problems, missing


def run_inspection(
    source: Path, inspect_sh: Path, root: Path, *, show_xfails: bool = False
) -> int:
    """Run PyCharm in isolation, with a failure control for every requested check."""
    try:
        expected = load_expected_failures(source)
    except (TypeError, ValueError, SyntaxError) as error:
        print(f"Invalid PyCharm xfail manifest: {error}", file=sys.stderr)
        return 2
    project, source_lines = prepare_project(source, root, inspect_sh)
    profile = et.Element("profile", version="1.0")
    et.SubElement(profile, "option", name="myName", value="Alternative Type Probe")
    for inspection in INSPECTIONS:
        et.SubElement(
            profile,
            "inspection_tool",
            {
                "class": inspection,
                "enabled": "true",
                "level": "WARNING",
                "enabled_by_default": "true",
            },
        )
    write_xml(root / "profile.xml", profile)
    vmoptions = root / "pycharm.vmoptions"
    vmoptions.write_text(
        "\n".join(
            f"-Didea.{name}.path={root / name}"
            for name in ("config", "system", "log", "plugins")
        )
        + "\n"
    )
    result = subprocess.run(
        [
            str(inspect_sh),
            str(project),
            str(root / "profile.xml"),
            str(root / "results"),
            "-v0",
        ],
        env={**os.environ, "PYCHARM_VM_OPTIONS": str(vmoptions)},
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        print("PyCharm inspect.sh failed.", file=sys.stderr)
        print((result.stderr + result.stdout)[-8000:], file=sys.stderr)
        return 2
    try:
        problems, missing = collect_problems(root / "results", source_lines)
    except (et.ParseError, ValueError) as error:
        print(f"Invalid PyCharm inspection results: {error}", file=sys.stderr)
        return 2
    if missing:
        print(
            "PyCharm did not report the failure controls for: " + ", ".join(missing),
            file=sys.stderr,
        )
        return 2
    failures = apply_expected_failures(problems, expected, show_xfails=show_xfails)
    for problem in failures:
        print(problem)
    return int(bool(failures))


def main() -> int:
    """Keep a clean inspection silent and remove all disposable IDE state."""
    source, inspect_sh = map(Path, sys.argv[1:3])
    show_xfails = sys.argv[3:] == ["--show-xfails"]
    if sys.argv[3:] and not show_xfails:
        print(
            "Unknown argument; use --show-xfails to list recognised gaps",
            file=sys.stderr,
        )
        return 2
    with tempfile.TemporaryDirectory(prefix="alternative-pycharm-type-probes.") as temp:
        return run_inspection(
            source.resolve(), inspect_sh.resolve(), Path(temp), show_xfails=show_xfails
        )


if __name__ == "__main__":
    sys.exit(main())
