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

python="${PYCHARM_PYTHON:-${repo_root}/.venv/bin/python}"
if [[ ! -x "${python}" ]]; then
  printf 'Python environment not found. Run uv sync --dev first or set PYCHARM_PYTHON.\n' >&2
  exit 2
fi

exec "${python}" "${script_dir}/pycharm_type_probes.py" "${repo_root}" "${inspect_sh}" "$@"
