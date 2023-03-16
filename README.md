# VSC Software Stack

Central repository of easyconfigs used in the software installations on VSC clusters.

## Structure

The organization of this repo is structured on standard git branches, each one providing a different degree of reliability:

* `vsc`: main branch with software installations validated by multiple VSC sites and tested
* `site-*`: software installations validated by a single site (not necessarily tested)
* `wip`: software installations that are work-in-progress

## Bootstrap

Users of this repo are encouraged to work with git worktrees. This approach allows to have all easyconfigs available in the VSC Software Stack across all its branches under a single folder in your local system.

1. Create a new folder for this repo
```bash
$ mkdir vsc-software-stack
```

2. Clone the bare repository (we keep it in a hidden folder as it won't be used directly)
```bash
$ git clone --bare git@github.com:vscentrum/vsc-software-stack.git vsc-software-stack/.bare
```

3. Point git to the bare repo from the root folder
```bash
$ echo "gitdir: ./.bare" > vsc-software-stack/.git
```

4. Add worktrees for each branch in their own folder
```bash
$ cd vsc-software-stack
$ git worktree add vsc
$ git worktree add wip
```
