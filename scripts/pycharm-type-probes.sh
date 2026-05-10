#!/usr/bin/env bash
set -Eeuo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(cd -- "${script_dir}/.." && pwd -P)"

inspect_sh="${PYCHARM_INSPECT_SH:-}"
if [[ -z "${inspect_sh}" ]]; then
  toolbox_inspect="${HOME}/.local/share/JetBrains/Toolbox/apps/pycharm-professional/bin/inspect.sh"
  if [[ -x "${toolbox_inspect}" ]]; then
    inspect_sh="${toolbox_inspect}"
  elif command -v inspect.sh >/dev/null 2>&1; then
    inspect_sh="$(command -v inspect.sh)"
  fi
fi

if [[ -z "${inspect_sh}" || ! -x "${inspect_sh}" ]]; then
  printf 'PyCharm inspect.sh was not found. Set PYCHARM_INSPECT_SH to its absolute path.\n' >&2
  exit 2
fi

tmp_root="$(mktemp -d "${TMPDIR:-/tmp}/alternative-pycharm-type-probes.XXXXXXXX")"
cleanup() {
  case "${tmp_root}" in
    "${TMPDIR:-/tmp}"/alternative-pycharm-type-probes.*)
      rm -rf -- "${tmp_root}"
      ;;
  esac
}
trap cleanup EXIT

profile="${tmp_root}/profile.xml"
results="${tmp_root}/results"
vmoptions="${tmp_root}/pycharm.vmoptions"
stdout_log="${tmp_root}/inspect.stdout"
stderr_log="${tmp_root}/inspect.stderr"
problems="${tmp_root}/problems.xml"

cat >"${profile}" <<'XML'
<component name="InspectionProjectProfileManager">
  <profile version="1.0">
    <option name="myName" value="Alternative Type Probe" />
    <inspection_tool class="PyAssertTypeInspection" enabled="true" level="WARNING" enabled_by_default="true" />
    <inspection_tool class="PyTypeCheckerInspection" enabled="true" level="WARNING" enabled_by_default="true" />
    <inspection_tool class="PyUnresolvedReferencesInspection" enabled="true" level="WARNING" enabled_by_default="true" />
  </profile>
</component>
XML

cat >"${vmoptions}" <<EOF
-Didea.config.path=${tmp_root}/config
-Didea.system.path=${tmp_root}/system
-Didea.log.path=${tmp_root}/log
-Didea.plugins.path=${tmp_root}/plugins
EOF

if ! PYCHARM_VM_OPTIONS="${vmoptions}" "${inspect_sh}" "${repo_root}" "${profile}" "${results}" -v0 >"${stdout_log}" 2>"${stderr_log}"; then
  printf 'PyCharm inspect.sh failed.\n' >&2
  if [[ -s "${stderr_log}" ]]; then
    printf '\n[stderr]\n' >&2
    tail --lines=80 "${stderr_log}" >&2
  fi
  if [[ -s "${stdout_log}" ]]; then
    printf '\n[stdout]\n' >&2
    tail --lines=80 "${stdout_log}" >&2
  fi
  exit 2
fi

if [[ ! -d "${results}" ]]; then
  printf 'PyCharm inspect.sh did not create an inspection results directory.\n' >&2
  exit 2
fi

: >"${problems}"
# PyNestedDecoratorsInspection is intentionally excluded here. PyCharm reports
# a false positive for correctly typed decorators stacked over classmethod or
# staticmethod; see PyNestedDecoratorsInspection-issue.md and related YouTrack
# issue PY-34368.
for inspection in \
  PyAssertTypeInspection \
  PyTypeCheckerInspection \
  PyUnresolvedReferencesInspection
do
  report="${results}/${inspection}.xml"
  if [[ ! -f "${report}" ]]; then
    continue
  fi

  normalized_report="${tmp_root}/${inspection}.normalized.xml"
  sed -e 's#<problem>#\
<problem>#g' -e 's#</problem>#</problem>\
#g' "${report}" >"${normalized_report}"

  awk -v inspection="${inspection}" '
    /<problem>/ {
      in_problem = 1
      relevant = 0
      block = $0 ORS
      next
    }
    in_problem {
      block = block $0 ORS
      if ($0 ~ /typing_tests\/type_probes\.py/) {
        relevant = 1
      }
      if ($0 ~ /<\/problem>/) {
        if (relevant) {
          print "<!-- " inspection " -->"
          printf "%s", block
        }
        in_problem = 0
        relevant = 0
        block = ""
      }
    }
  ' "${normalized_report}" >>"${problems}"
done

if [[ -s "${problems}" ]]; then
  cat "${problems}"
  exit 1
fi
