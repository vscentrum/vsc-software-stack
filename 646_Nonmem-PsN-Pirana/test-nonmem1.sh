#!/usr/bin/env bash
set -euo pipefail

if [ ! -f "$EBROOTNONMEM/license/nonmem.lic" ]; then
  echo "Missing license file: $EBROOTNONMEM/license/nonmem.lic" >&2
  exit 1
fi

workdir=$(mktemp -d)
trap 'rm -rf "$workdir"' EXIT

cp "$EBROOTNONMEM"/util/CONTROL5 "$workdir"/
cp "$EBROOTNONMEM"/util/THEOPP "$workdir"/

cd "$workdir"
nmfe76 CONTROL5 report5.txt

test -s report5.txt
grep -qi "objective function" report5.txt
grep -qi "MINIMUM VALUE OF OBJECTIVE FUNCTION" report5.txt || true

echo "NONMEM smoke test completed."
echo "Workdir: $workdir"
echo "Report:  $workdir/report5.txt"
grep -i "objective function" report5.txt | tail -5