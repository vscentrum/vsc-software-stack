#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./test_fftw.sh [FFTW_MODULE]
# Examples:
#   ./test_fftw.sh FFTW/3.3.10-NVHPC-25.3
#   ./test_fftw.sh
#
# If you pass a module name, the script will try to "module purge" + "module load".

# MOD="${1:-}"

# if command -v module >/dev/null 2>&1; then
#   if [[ -n "$MOD" ]]; then
#     module purge || true
#     module load "$MOD"
#   fi
# fi

if ! command -v pkg-config >/dev/null 2>&1 && ! command -v pkgconf >/dev/null 2>&1; then
  echo "ERROR: neither pkg-config nor pkgconf found in PATH" >&2
  exit 1
fi

PKGCONFIG="$(command -v pkg-config || command -v pkgconf)"

cat > test_fftw.c <<'EOF'
#include <stdio.h>
#include <math.h>
#include <fftw3.h>

int main(void) {
  const int N = 8;

  fftw_complex in[N], out[N];
  for (int i = 0; i < N; i++) {
    in[i][0] = 1.0;  // real
    in[i][1] = 0.0;  // imag
  }

  fftw_plan p = fftw_plan_dft_1d(N, in, out, FFTW_FORWARD, FFTW_ESTIMATE);
  if (!p) {
    fprintf(stderr, "FFTW plan creation failed\n");
    return 2;
  }
  fftw_execute(p);
  fftw_destroy_plan(p);

  // DFT of constant-1 signal:
  // out[0] should be N + 0i, and out[k>0] should be ~0.
  double tol = 1e-9;
  if (fabs(out[0][0] - (double)N) > tol || fabs(out[0][1]) > tol) {
    fprintf(stderr, "Unexpected out[0]=(%g,%g), expected (%d,0)\n", out[0][0], out[0][1], N);
    return 3;
  }
  for (int k = 1; k < N; k++) {
    if (fabs(out[k][0]) > tol || fabs(out[k][1]) > tol) {
      fprintf(stderr, "Unexpected out[%d]=(%g,%g), expected ~0\n", k, out[k][0], out[k][1]);
      return 4;
    }
  }

  printf("OK: FFTW DFT sanity test passed (N=%d)\n", N);
  return 0;
}
EOF

# Prefer pkg-config, fallback to manual -lfftw3 if not found.
CFLAGS="$($PKGCONFIG --cflags fftw3 2>/dev/null || true)"
LIBS="$($PKGCONFIG --libs fftw3 2>/dev/null || true)"

CC="${CC:-cc}"
BIN="./test_fftw"

if [[ -n "$LIBS" ]]; then
  echo "Compiling with pkg-config: $CC $CFLAGS test_fftw.c $LIBS -lm -o $BIN"
  $CC $CFLAGS test_fftw.c $LIBS -lm -o "$BIN"
else
  echo "WARNING: pkg-config could not find 'fftw3'. Trying manual link: -lfftw3"
  echo "Compiling: $CC test_fftw.c -lfftw3 -lm -o $BIN"
  $CC test_fftw.c -lfftw3 -lm -o "$BIN"
fi

echo "Running $BIN"
"$BIN"
