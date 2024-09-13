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
EB_EASYCONFIGS="${1:-../easybuild}"

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

# check directory structure
[ -d "$SITE_EASYCONFIGS" ] || fail "Site easyconfig repo not found: $SITE_EASYCONFIGS"
[ -d "$EB_EASYCONFIGS" ] || fail "Upstream easyconfig repo not found: $EB_EASYCONFIGS"

# sync site repo with remote
git pull origin "$SITE_REPO" || fail "Failed to sync site repo with remote"

while read -r site_file; do
    site_filename=$(basename "$site_file")
    echo "=== $site_filename"
    eb_file=$(find -L "$EB_EASYCONFIGS" -name "$site_filename" -print)
    if [ -z "$eb_file" ]; then
        echo "    > Not found upstream"
    else
        echo "    > Found upstream"
        # check the diff between both files
        if diff -q "$site_file" "$eb_file" 1>/dev/null; then
            echo "    > Files are equal"
            # remove site copy of the file
            (git_repo_remove "$site_file" 1>/dev/null && echo "    > Removed from local site repo") \
                || fail "Failed to remove file from site repo: $site_file"
        else
            echo "    > Files differ"
        fi
    fi
done < <(find "$SITE_EASYCONFIGS" -type f -print)

echo "!!! Verify changes in git log and push to remote with:"
echo "    git push origin $SITE_REPO"
