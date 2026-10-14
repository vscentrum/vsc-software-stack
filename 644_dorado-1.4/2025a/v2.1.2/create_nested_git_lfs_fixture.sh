#!/usr/bin/env bash
# Create a local main -> submodule -> nested submodule Git LFS test fixture
# for EasyBuild's get_source_tarball_from_git().
set -euo pipefail

if ! command -v git-lfs >/dev/null 2>&1; then
    echo 'ERROR: git-lfs is required to CREATE the fixture. Load git-lfs/3.7.1 first.' >&2
    exit 1
fi

root=$(mktemp -d "${TMPDIR:-/tmp}/easybuild-nested-lfs.XXXXXX")
mkdir -p "$root/remotes" "$root/work" "$root/sources"
# Git disables the file transport for submodules by default for security.
# Limit the override to this disposable, entirely local fixture.
export GIT_ALLOW_PROTOCOL=file
export GIT_LFS_SKIP_SMUDGE=1

init_work_repo() {
    git init -q -b main "$1"
    git -C "$1" config user.name 'EasyBuild LFS Test'
    git -C "$1" config user.email 'easybuild-lfs-test@example.invalid'
}

for repo in eb-lfs-leaf eb-lfs-mid eb-lfs-top; do
    git init -q --bare -b main "$root/remotes/$repo.git"
    init_work_repo "$root/work/$repo"
    git -C "$root/work/$repo" remote add origin "file://$root/remotes/$repo.git"
done

# Deepest repository: actual LFS object, not merely an LFS pointer example.
leaf="$root/work/eb-lfs-leaf"
git -C "$leaf" lfs install --local >/dev/null
git -C "$leaf" lfs track '*.bin' >/dev/null
printf 'EASYBUILD_REAL_LFS_DATA_FROM_NESTED_SUBMODULE\n' > "$leaf/real-lfs.bin"
git -C "$leaf" add .gitattributes real-lfs.bin
git -C "$leaf" commit -qm 'Add tracked Git LFS object'
# Abort if the file was committed as plain Git content rather than an LFS pointer.
git -C "$leaf" show HEAD:real-lfs.bin | grep -Fqx 'version https://git-lfs.github.com/spec/v1' \
    || { echo 'LFS pointer not created correctly' >&2; exit 1; }
git -C "$leaf" push -q -u origin main
git -C "$leaf" lfs push --all origin >/dev/null

# Middle repository contains the LFS repository as a nested submodule.
mid="$root/work/eb-lfs-mid"
git -C "$mid" submodule add -q "file://$root/remotes/eb-lfs-leaf.git" nested-leaf
git -C "$mid" add .gitmodules nested-leaf
git -C "$mid" commit -qm 'Add nested leaf submodule'
git -C "$mid" push -q -u origin main

# Top-level repository contains the middle submodule.
top="$root/work/eb-lfs-top"
git -C "$top" submodule add -q "file://$root/remotes/eb-lfs-mid.git" nested-mid
git -C "$top" add .gitmodules nested-mid
git -C "$top" commit -qm 'Add middle submodule'
git -C "$top" tag v1.0
git -C "$top" push -q -u origin main
git -C "$top" push -q origin v1.0

cat > "$root/EBNestedLFSTest-1.0.eb" <<EASYCONFIG
easyblock = 'ConfigureMake'
name = 'EBNestedLFSTest'
version = '1.0'
homepage = 'https://github.com/easybuilders/easybuild-framework'
description = 'Temporary, local Git LFS nested-submodule fetch test.'
toolchain = SYSTEM
source_deps = [('git-lfs', '3.7.1', '', SYSTEM)]
sources = [{
    'filename': SOURCE_TAR_XZ,
    'git_config': {
        'url': 'file://$root/remotes',
        'repo_name': 'eb-lfs-top',
        'tag': 'v1.0',
        'recursive': True,
    },
}]
checksums = [None]
moduleclass = 'tools'
EASYCONFIG

cat > "$root/verify.sh" <<'VERIFY'
#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")" && pwd)
archive=$(find "$root/sources" -type f -name 'EBNestedLFSTest-1.0.tar.xz' -print -quit)
if [ -z "$archive" ]; then echo 'No generated EasyBuild source archive found' >&2; exit 1; fi
member=$(tar -tJf "$archive" | grep '/nested-mid/nested-leaf/real-lfs.bin$')
if [ -z "$member" ]; then echo 'Nested LFS file not found in archive' >&2; exit 1; fi
actual=$(tar -xJOf "$archive" "$member")
expected='EASYBUILD_REAL_LFS_DATA_FROM_NESTED_SUBMODULE'
if [ "$actual" != "$expected" ]; then
    echo "FAIL: nested LFS file was not hydrated: $actual" >&2
    exit 1
fi
echo "PASS: nested Git LFS object hydrated in $archive"
VERIFY
chmod +x "$root/verify.sh"

printf '\nFixture created in: %s\n\n' "$root"
printf 'To run the EasyBuild fetch test (unload git-lfs from your shell first):\n'
printf '  module unload git-lfs 2>/dev/null || true\n'
printf '  GIT_ALLOW_PROTOCOL=file eb %q --stop=fetch --sourcepath=%q\n' \
    "$root/EBNestedLFSTest-1.0.eb" "$root/sources"
printf '\nThen validate downloaded content:\n  %q\n' "$root/verify.sh"
