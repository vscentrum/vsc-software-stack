#!/usr/bin/env bash
set -euo pipefail

mod="${1:-FreeSurfer/8.1.0-rocky9_x86_64}"

echo
echo "== Basic env =="
for v in FREESURFER_HOME FREESURFER SUBJECTS_DIR MNI_DIR FSFAST_HOME FMRI_ANALYSIS_DIR; do
  printf "  %-18s %s\n" "$v" "${!v-<unset>}"
done
test -n "${FREESURFER_HOME-}" && test -d "$FREESURFER_HOME"
test -x "$FREESURFER_HOME/bin/recon-all"

echo
echo "== Versions / help (no license needed) =="
"$FREESURFER_HOME/bin/recon-all" -version 2>/dev/null | sed 's/^/  /' || true
"$FREESURFER_HOME/bin/mri_convert" --version 2>/dev/null | sed 's/^/  /' || "$FREESURFER_HOME/bin/mri_convert" --help >/dev/null
"$FREESURFER_HOME/bin/tkregister2" --help >/dev/null 2>&1 || true

echo
echo "== License file (optional) =="
if [[ -n "${FS_LICENSE-}" ]]; then
  echo "  FS_LICENSE=$FS_LICENSE"
  test -r "$FS_LICENSE" && echo "  OK: readable"
else
  echo "  FS_LICENSE not set (fine for this smoketest)"
fi
if [[ -r "$FREESURFER_HOME/.license" ]]; then
  echo "  Found: $FREESURFER_HOME/.license"
else
  echo "  No in-tree .license (fine if users set FS_LICENSE)"
fi

echo
echo "== MCR wiring (FreeSurfer 8.x expects MCRv97) =="
if [[ -d "$FREESURFER_HOME/MCRv97" ]]; then
  echo "  OK: $FREESURFER_HOME/MCRv97 exists"
  if [[ -L "$FREESURFER_HOME/MCRv97" ]]; then
    echo "  symlink -> $(readlink -f "$FREESURFER_HOME/MCRv97")"
  fi
else
  echo "  ERROR: missing $FREESURFER_HOME/MCRv97"
  exit 1
fi

echo
echo "== Shared library sanity (headless-safe) =="
check_bins=(
  "$FREESURFER_HOME/bin/recon-all"
  "$FREESURFER_HOME/bin/mri_convert"
  "$FREESURFER_HOME/bin/mri_info"
)
for b in "${check_bins[@]}"; do
  if [[ -x "$b" ]]; then
    miss=$(ldd "$b" 2>/dev/null | awk '/not found/{print $1}' || true)
    if [[ -n "$miss" ]]; then
      echo "  MISSING libs for $(basename "$b"):"
      echo "$miss" | sed 's/^/    /'
      exit 1
    else
      echo "  OK: $(basename "$b")"
    fi
  fi
done

echo
echo "== Minimal file roundtrip (no license) =="
tmpd=$(mktemp -d)
trap 'rm -rf "$tmpd"' EXIT
# Create a tiny dummy volume (16^3) using mri_convert's ability to write formats
# We'll use mri_info on a generated mgz to confirm pipeline basics
# (If your build lacks this behavior, the script will still pass earlier checks.)
dd if=/dev/zero of="$tmpd/zeros.raw" bs=1 count=$((16*16*16*2)) status=none || true
# Some FreeSurfer builds include mri_convert raw->mgz support; try, but don't fail hard.
if "$FREESURFER_HOME/bin/mri_convert" "$tmpd/zeros.raw" "$tmpd/zeros.mgz" >/dev/null 2>&1; then
  "$FREESURFER_HOME/bin/mri_info" "$tmpd/zeros.mgz" >/dev/null
  echo "  OK: mri_convert + mri_info"
else
  echo "  Skipped: raw->mgz conversion not supported in this build (not fatal)"
fi

echo
echo "== Done: FreeSurfer smoketest PASS =="
