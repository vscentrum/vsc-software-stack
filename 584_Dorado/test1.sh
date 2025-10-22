#!/usr/bin/env bash
set -euo pipefail

# --- Configuration (optional e2e test) ---
# Provide these to run a short basecalling test; otherwise it’s skipped.
# MODEL_DIR: directory containing a valid dorado model (e.g. dna_r10.4.1_e8.2_400bps_fast)
# POD5_DIR:  directory with a few .pod5 files (<= ~10 files recommended)
# Example:
#   export MODEL_DIR=/path/to/models/dna_r10.4.1_e8.2_400bps_fast
#   export POD5_DIR=/path/to/tiny_sample_pod5
MODEL_DIR="${MODEL_DIR:-}"
POD5_DIR="${POD5_DIR:-}"
OUTDIR="${OUTDIR:-$(mktemp -d)}"

# --- Helpers ---
pass() { printf "[ OK ] %s\n" "$*"; }
fail() { printf "[FAIL] %s\n" "$*" >&2; exit 1; }

require() {
  command -v "$1" >/dev/null 2>&1 || fail "Missing required command: $1"
}

# --- 0) Basic presence ---
require dorado
pass "dorado is on PATH: $(command -v dorado)"

# --- 1) Binary and linked libs resolve (no missing libs in ldd) ---
if command -v ldd >/dev/null 2>&1; then
  if ! ldd "$(command -v dorado)" | grep -q "not found"; then
    pass "ldd shows no missing shared libraries for dorado"
  else
    ldd "$(command -v dorado)"; fail "Missing shared libraries (see above)"
  fi
else
  pass "ldd not available; skipping shared-library check"
fi

# --- 2) CUDA visibility (optional but useful) ---
if command -v nvidia-smi >/dev/null 2>&1; then
  nvidia-smi -L >/dev/null 2>&1 && pass "nvidia-smi sees GPU(s)" || fail "nvidia-smi found no GPUs"
else
  pass "nvidia-smi not present; skipping GPU listing"
fi

# --- 3) PyTorch CUDA sanity (matches your toolchain) ---
if command -v python >/dev/null 2>&1; then
  python - <<'PY'
import os, torch, sys
print("torch_version:", torch.__version__)
print("cuda_available:", torch.cuda.is_available())
print("cuda_version:", getattr(torch.version, "cuda", None))
print("device_count:", torch.cuda.device_count())
# fastest failure if CUDA not working: allocate a 1-element tensor on cuda:0
if torch.cuda.is_available():
    t = torch.tensor([1.0], device="cuda:0")
    print("cuda_tensor_ok:", float(t.item()) == 1.0)
PY
  pass "PyTorch CUDA check executed"
else
  pass "python not present; skipping PyTorch CUDA check"
fi

# --- 4) Dorado CLI smoke tests ---
dorado --version >/dev/null 2>&1 && pass "dorado --version"
dorado basecaller --help >/dev/null 2>&1 && pass "dorado basecaller --help"

# Some builds ship additional subcommands; harmless if missing.
for sub in file-info model-download demux duplex correct polish; do
  if dorado "$sub" --help >/dev/null 2>&1; then
    pass "dorado $sub --help"
  fi
done

# --- 5) Optional end-to-end basecalling (tiny run) ---
# This proves HTS I/O + Torch + CUDA + Dorado pipeline, if sample + model provided.
if [[ -n "$MODEL_DIR" && -n "$POD5_DIR" ]]; then
  echo "[INFO] Running short basecalling test…"
  mkdir -p "$OUTDIR"
  # Notes:
  # - keep it small; adjust flags to your local policy/perf
  # - --device cpu is a good fallback if you want a non-GPU check
  # If your site prefers CPU smoke: add "--device cpu" below.
  set -x
  dorado basecaller "$MODEL_DIR" "$POD5_DIR" \
    --batchsize 1 \
    --chunks 16 \
    --emit-fastq \
    > "$OUTDIR/out.fastq"
  set +x

  # Validate output looks like FASTQ
  if head -n 1 "$OUTDIR/out.fastq" | grep -q '^@'; then
    pass "Basecalling produced FASTQ: $OUTDIR/out.fastq"
  else
    fail "Basecalling output does not look like FASTQ"
  fi

  # Optional: BAM/SAM check (only if you emit BAM/SAM). Example:
  # dorado basecaller "$MODEL_DIR" "$POD5_DIR" > "$OUTDIR/out.bam"
  # if command -v samtools >/dev/null 2>&1; then
  #   samtools quickcheck "$OUTDIR/out.bam" && pass "BAM passes samtools quickcheck" \
  #     || fail "BAM failed samtools quickcheck"
  # fi
else
  echo "[INFO] Skipping end-to-end basecalling (set MODEL_DIR and POD5_DIR to enable)."
fi

echo
pass "All smoke tests completed."
echo "Output dir: $OUTDIR"
