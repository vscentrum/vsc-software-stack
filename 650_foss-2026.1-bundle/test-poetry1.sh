#!/usr/bin/env bash
set -euo pipefail

export POETRY_KEYRING_ENABLED=false
PYTHON_BIN="${1:-python3}"
KEEP="${KEEP:-0}"

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || { echo "ERROR: missing command: $1" >&2; exit 1; }
}

run() {
  echo "+ $*"
  "$@"
}

need_cmd poetry
need_cmd "$PYTHON_BIN"

# echo "== Poetry smoke test =="
# run poetry --version
# run "$PYTHON_BIN" --version

TMPDIR="$(mktemp -d)"
PROJECT_DIR="$TMPDIR/poetry-smoke-project"

cleanup() {
  if [ "$KEEP" = "1" ]; then
    echo "Keeping test project: $PROJECT_DIR"
  else
    rm -rf "$TMPDIR"
  fi
}
trap cleanup EXIT

echo "== Creating temporary Poetry project =="
run poetry new "$PROJECT_DIR"

cd "$PROJECT_DIR"

echo "== Configuring in-project virtualenv =="
run poetry config virtualenvs.in-project true --local
run poetry env use "$PYTHON_BIN"

echo "== Adding test dependency =="
run poetry add --group dev pytest

echo "== Writing smoke test =="
cat > tests/test_smoke.py <<'PY'
import importlib

def test_package_imports():
    assert importlib.import_module("poetry_smoke_project") is not None
PY

echo "== Installing project =="
run poetry install

echo "== Checking Poetry-managed Python =="
run poetry run python -c 'import sys; print(sys.executable); print(sys.version)'

echo "== Running tests =="
run poetry run pytest -q

echo "== Validating pyproject.toml =="
run poetry check

echo "== Building package =="
run poetry build

echo "== Inspecting build artifacts =="
ls -lah dist
test -n "$(find dist -maxdepth 1 -name '*.whl' -print -quit)"
test -n "$(find dist -maxdepth 1 -name '*.tar.gz' -print -quit)"

echo "SUCCESS: Poetry smoke test passed."