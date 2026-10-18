"""Inspect a disposable project and require proof that each inspection ran."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys
import sysconfig
import tempfile
import xml.etree.ElementTree as et


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


def collect_problems(results: Path, source_lines: int) -> tuple[list[str], list[str]]:
    """Separate source diagnostics from controls and reject incomplete inspections."""
    problems: list[str] = []
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
                    problems.append(
                        f"typing_tests/type_probes.py:{line}: {inspection}: {description}"
                    )
        if not control_seen:
            missing.append(inspection)
    return problems, missing


def run_inspection(source: Path, inspect_sh: Path, root: Path) -> int:
    """Run PyCharm in isolation, with a failure control for every requested check."""
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
    for problem in problems:
        print(problem)
    return int(bool(problems))


def main() -> int:
    """Keep a clean inspection silent and remove all disposable IDE state."""
    source, inspect_sh = map(Path, sys.argv[1:])
    with tempfile.TemporaryDirectory(prefix="alternative-pycharm-type-probes.") as temp:
        return run_inspection(source.resolve(), inspect_sh.resolve(), Path(temp))


if __name__ == "__main__":
    sys.exit(main())
