#!/usr/bin/env bash
set -euo pipefail

bindir="${1:-${EBROOTFREESURFER:-}/bin}"

if [[ -z "${bindir}" || ! -d "${bindir}" ]]; then
    echo "ERROR: bin directory not found: ${bindir}" >&2
    exit 1
fi

failed=0

while IFS= read -r -d '' f; do
    if file -L "$f" | grep -q 'ELF' && ldd "$f" 2>&1 | grep -q 'not found'; then
        echo "$f"
        failed=1
    fi
done < <(find -L "$bindir" -maxdepth 1 \( -type f -o -type l \) -print0 | sort -z)

if [[ "$failed" -eq 0 ]]; then
    echo "No missing shared libraries found in $bindir"
else
    exit 1
fi