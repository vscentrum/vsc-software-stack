#!/bin/bash
set -euo pipefail

echo "== DIA-NN runtime smoke test =="

: "${EBROOTDIAMINNN:?Load the DIA-NN module first}"

BIN="$EBROOTDIAMINNN/diann-linux"
STATS="$EBROOTDIAMINNN/diann-stats.py"

echo "-- binary exists"
test -x "$BIN"

echo "-- stats script exists"
test -f "$STATS"

echo "-- libstdc++ resolution"
ldd "$BIN" | grep 'libstdc++.so.6 =>'

if ldd "$BIN" | grep -q 'libstdc++.so.6 => /lib64/libstdc++.so.6'; then
    echo "ERROR: libstdc++.so.6 still resolves to /lib64"
    exit 1
fi

echo "-- DIA-NN help"
"$BIN" --help >/tmp/diann-help.txt 2>&1 || {
    cat /tmp/diann-help.txt
    exit 1
}
head -n 20 /tmp/diann-help.txt

echo "-- Python deps + stats script import"
python - <<'PY'
import os, runpy
import polars, numpy, matplotlib
root = os.environ["EBROOTDIAMINNN"]
runpy.run_path(os.path.join(root, "diann-stats.py"), run_name="__test__")
print("Python side OK")
PY

echo "OK"