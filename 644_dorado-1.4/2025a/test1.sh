#!/usr/bin/env bash
set -euo pipefail

echo "[INFO] PATH: $PATH"
echo "[INFO] dorado: $(command -v dorado)"

echo "[TEST] top-level help"
dorado -h >/dev/null

for subcmd in basecaller summary download duplex aligner correct polish variant; do
    echo "[TEST] dorado ${subcmd} -h"
    dorado "${subcmd}" -h >/dev/null
done

echo "[TEST] basic executable linkage"
ldd "$(command -v dorado)" >/dev/null

if command -v nvidia-smi >/dev/null 2>&1; then
    echo "[INFO] NVIDIA GPUs visible:"
    nvidia-smi -L || true
fi

echo "[OK] Dorado basic smoke test passed"