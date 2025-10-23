# How to do a release

1. Make a new branch, create a commit on it that changes `delta/_version.py`
   and updates `CHANGELOG.md`
2. Optional: update also `pixi.lock`
3. Create a merge request, ensure that tests pass
4. Merge it to main
5. Create and push a tag on the commit with the format `vX.Y.ZAAA` with `X`
   being the major version, `Y` the minor version, `Z` the patch version, and
   `AAA` optional pre-release identifiers

Pushing the tag will trigger the release jobs, one for GitLab and one for PyPI.
