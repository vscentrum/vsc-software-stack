#!/bin/bash
#
# Script to automatically remove from site-vub repo any easyconfig and
# patch files already merged upstream in EasyBuild.
#
# usage: clean-site-vub.sh [path to local easyconfig repo]
# (execute from top directory of site-vub git repo)
#

SITE_REPO="site-vub"
SITE_EASYCONFIGS="easyconfigs"
[ -d "$SITE_EASYCONFIGS" ] || fail "Site easyconfig repo not found: $SITE_EASYCONFIGS"
EB_EASYCONFIGS="${1:-../easybuild}"
[ -d "$EB_EASYCONFIGS" ] || fail "Upstream easyconfig repo not found: $EB_EASYCONFIGS"

function fail () {
    echo "$1" >&2
    exit "${2-1}"
}

function git_repo_remove () {
    # delete file from git repo locally and remotely
    old_file="${1}"
    [ -f "$old_file" ] || fail "File to be removed not found: $old_file"

    git rm "$old_file"
    git commit -m "Merged upstream: $(basename "$old_file")"
}

function find_easyconfig () {
    # find easyconfig files in repository
    # prefer `fd` over `find`
    if hash fd 2>/dev/null; then
        fd "^${1}$" "$EB_EASYCONFIGS"
    else
        find -L "$EB_EASYCONFIGS" -name "$1" -print
    fi
}

# sync site repo with remote
git pull origin "$SITE_REPO" || fail "Failed to sync site repo with remote"

while read -r site_file; do
    site_filename=$(basename "$site_file")
    echo ""
    echo "=== $site_filename"
    eb_file=$(find_easyconfig "$site_filename")
    if [ -z "$eb_file" ]; then
        echo "    > Not found upstream"
    else
        echo "    > Found upstream"
        # check the diff between both files
        difftxt=$(diff -u "$site_file" "$eb_file")
        if [ -z "$difftxt" ]; then
            echo "    > Files are equal"
            remove site copy of the file
            if git_repo_remove "$site_file" 1>/dev/null; then
                echo "    > Removed from local site repo"
            else
                fail "Failed to remove file from site repo: $site_file"
            fi
        else
            echo "    > Files differ"
            echo "$difftxt"
        fi
    fi
done < <(find "$SITE_EASYCONFIGS" -type f -print)

echo "!!! Verify changes in git log and push to remote with:"
echo "    git push origin $SITE_REPO"
