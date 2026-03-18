#!/usr/bin/env bash
set -euo pipefail

bindir="${1:-${EBROOTFREESURFER:-}/bin}"

if [[ -z "${bindir}" || ! -d "${bindir}" ]]; then
    echo "ERROR: bin directory not found: ${bindir}" >&2
    exit 1
fi

found_missing=0

while IFS= read -r -d '' f; do
    if file -L "$f" | grep -q 'ELF'; then
        out="$(ldd "$f" 2>&1 || true)"
        if grep -q 'not found' <<< "$out"; then
            echo "=== $f ==="
            echo "$out"
            echo
            found_missing=1
        fi
    fi
done < <(find -L "$bindir" -maxdepth 1 \( -type f -o -type l \) -print0 | sort -z)

if [[ "$found_missing" -eq 0 ]]; then
    echo "No missing shared libraries found in $bindir"
else
    exit 1
fi