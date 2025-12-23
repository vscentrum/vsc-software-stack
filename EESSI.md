EESSI
=====

EESSI repo (`software-layer`)
-----------------------------

1. Fork the official repo
    - https://github.com/EESSI/software-layer/fork
2. Download your repo
    ```bash
    git clone git@github.com:pavelToman/software-layer.git
    ```

Setup of the EESSI environment on HPC
-------------------------------------

- version `2023.06` (for `2023b`/`13.2.0` and older)
    ```bash
    unset PYTHONPATH && \
    unset MODULEPATH && \
    source /cvmfs/software.eessi.io/versions/2023.06/init/bash && \
    module load EasyBuild && \
    module load EESSI-extend/2023.06-easybuild
    ```

- version `2025.06` (for `2024a`/`13.3.0` and newer)
    ```bash
    unset PYTHONPATH && \
    unset MODULEPATH && \
    source /cvmfs/software.eessi.io/versions/2025.06/init/bash && \
    module load EasyBuild && \
    module load EESSI-extend/2025.06-easybuild
    ```

Missing dependencies and build test on top of EESSI
---------------------------------------------------

1. Find out whether the easyconfig already is in `5.1.x` (or newer version) or only in the `develop` brach of `easybuilders/easybuild-easyconfigs`
    - for example `Bandage-0.9.0-GCCcore-14.2.0.eb` only is in `develop`
        - https://github.com/easybuilders/easybuild-easyconfigs/blob/develop/easybuild/easyconfigs/b/Bandage/Bandage-0.9.0-GCCcore-14.2.0.eb
            - It is in the `develop` branch
        - https://github.com/easybuilders/easybuild-easyconfigs/blob/5.1.x/easybuild/easyconfigs/b/Bandage/Bandage-0.9.0-GCCcore-14.2.0.eb
            - 404 - page not found
    - If it is in develop only, we have to find it's `PR`.
        - top right click at `commit` and then click `PR`.
        - For `Bandage-0.9.0-GCCcore-14.2.0.eb` it is `24461`.
        - So we will have to add `--from-pr 24461` to the command.
2. Find out the missing dependencies in EESSI for the easyconfig
    - for example for `Bandage-0.9.0-GCCcore-14.2.0.eb`
        ```bash
        eb --from-pr 24461 --missing Bandage-0.9.0-GCCcore-14.2.0.eb
        ```
    - for easyconfigs, which already are in the `5.1.x` branch of `easybuilders/easybuild-easyconfigs`
        ```bash
        eb --missing Bandage-0.9.0-GCCcore-14.2.0.eb
        ```
    - The outup looks something like this.
        ```
        3 out of 20 required modules missing:

        * something1/version1 (blahblah1.eb)
        * something2/version2 (blahblah2.eb)
        * something3/version2 (blahblah3.eb)
        ```
        - This should be mentioned in the PR in `EESSI/software-layer`
3. Try whether the build succeeds on top of EESSI
    ```bash
    eb --from-pr 24461 Bandage-0.9.0-GCCcore-14.2.0.eb --rebuild --robot
    ```
    - If it succeeds, we can create the PR.

Creating the PR
---------------

1. Prepare your `software-layer` fork
    - on the Github page of our fork click `Sync fork` for the `main` branch
        - https://github.com/pavelToman/software-layer/tree/main
    - Go to the directory where your EESSI is cloned to (`software-layer`) and prepare a new branch for your easyconfig from the `main` branch.
        ```bash
        cd path/to/software-layer
        git checkout main
        git pull
        git checkout -b 2025.06-2024a-Bandage
        ```
3. Edit the easystack file.
    - for example the file `easystacks/software.eessi.io/2025.06/eessi-2025.06-eb-5.1.2-2024a.yml`
        - `2025.06` (version of EESSI for `2024a`/`13.3.0`)
        - `5.1.2` (currently latest out of the files in the directory)
        - `2024a` (`13.3.0` corresponds to `2024a`)
    - Add the file name at the end of the file
        - If the easyconfig is in `5.1.x` (or newer) branch of `easybuilders/easybuild-easyconfigs`
            ```yaml
              - Bandage-0.9.0-GCCcore-14.2.0.eb
            ```
        - If it is only in the `develop` branch of `easybuilders/easybuild-easyconfigs`
            ```yaml
              - Bandage-0.9.0-GCCcore-14.2.0.eb:
                  options:
                    # see https://github.com/easybuilders/easybuild-easyconfigs/pull/24461
                    from-commit: 755f553a71e40f7098cfc0d4329640a46f525181
            ```
            - Don't forget the colon at the end of the name of the easyconfigs.
            - Get the commit code by clicking on the commit (top right)
                - https://github.com/easybuilders/easybuild-easyconfigs/blob/develop/easybuild/easyconfigs/b/Bandage/Bandage-0.9.0-GCCcore-14.2.0.eb
4. Push to our `software-layer` branch
    - Commit the changes
        ```bash
        git add easystacks/software.eessi.io/2025.06/eessi-2025.06-eb-5.1.2-2024a.yml
        git commit -m '{2025.06}[2024a] Bandage 2.3.1'
        ```
            - the suggested name of the commit will be the commit message
            - `2025.06` (version of EESSI for `2024a`/`13.3.0`)
            - `2024a` (if the easyconfig is `2024a`/`13.3.0`)
            - `Bandage` names of the main easyconfigs
            - `2.3.1` versions of the main easyconfigs
    - Push te changes to the branch of our fork. (`--set-upstream` we have to add at first because it's not in remote yet)
        ```bash
        git push --set-upstream origin 2025.06-2024a-Bandage
        ```
    - For later changes we can do `git push` without `--set-upstream`.
5. Create the PR
    - Git will give us a link to the PR creation.
        - Add the list of missing dependencies to the PR description
            ```
            3 out of 20 required modules missing:

            * something1/version1 (blahblah1.eb)
            * something2/version2 (blahblah2.eb)
            * something3/version2 (blahblah3.eb)
            ```
        - Confirm the PR creation.
