Sandbox for VSC Central Software Installation project

### Policy

* Open issue per (sufficiently complex) software installation request.
  * Includes basic info + initial guidelines (toolchain, easyblock, etc.)
  * Place to discuss problems that pop up and get early feedback.
* Work-in-progress easyconfigs in separate subdirectories (one subdirectory per open issue).
* No pull requests (PRs) needed, no separate branches, just update `main` branch and push.
  ```
  # example for issue #12345
  git pull origin main
  mkdir 12345-example
  git add 12345-example
  git commit -m "add example (#12345)"
  git push origin main
  ```
* Open PR to [central easyconfigs repository](https://github.com/easybuilders/easybuild-easyconfigs) once easyconfigs are working.
* Cleanup: remove subdirectory and close issue when this PR is merged.

### Links

* EasyBuild documentation: https://docs.easybuild.io
* EasyBuild tutorial: https://easybuild.io/tutorial
* VSC Slack: https://vscentrum.slack.com
  * Requires invitation, ask Kenneth (HPC-UGent) or Sam (HPC-VUB), or anyone already in the VSC Slack.
