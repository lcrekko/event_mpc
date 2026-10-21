#!/usr/bin/env bash
set -euo pipefail
project_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_root"
export UV_CACHE_DIR="${UV_CACHE_DIR:-/workspace/.cache/uv}"
export XDG_CACHE_HOME="${XDG_CACHE_HOME:-/workspace/.cache}"
export MPLCONFIGDIR="${MPLCONFIGDIR:-$project_root/.mplconfig}"
if [ ! -x .venv/bin/python ]; then
  uv venv .venv --python python3.12
fi
uv pip install --python .venv/bin/python -r requirements-cloud.txt
uv pip check --python .venv/bin/python
.venv/bin/python scripts/environment_smoke.py
