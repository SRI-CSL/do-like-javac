#!/usr/bin/env bash

set -e
set -u
set -x
set -o pipefail

### This script runs the Checker Framework's tests that depend on
### dljc (i.e. this project's main script). It is intended to be used as part of a CI integration test.
### This script must be run from the top-level directory

### get plume-scripts so that we can use git-clone-related

if [ -d /tmp/"$USER"/plume-scripts ] ; then
  git -C /tmp/"$USER"/plume-scripts pull -q > /dev/null 2>&1
else
  mkdir -p /tmp/"$USER" && git -C /tmp/"$USER" clone --depth 1 -q https://github.com/plume-lib/plume-scripts.git
fi

### clone the CF. If there is a branch with the same name as this branch, git-clone-related will check out that branch.
rm -rf /tmp/"$USER"/checker-framework
/tmp/"$USER"/plume-scripts/git-clone-related typetools checker-framework /tmp/"$USER"/checker-framework
export CHECKERFRAMEWORK=/tmp/"$USER"/checker-framework

# see https://stackoverflow.com/questions/58033366/how-to-get-current-branch-within-github-actions/58035262
dljc_branch_name=${GITHUB_REF##*/}

### enforce that the CF is on the same branch that this copy of DLJC is - if git-clone-related's fallback
### branch (i.e. master for the CF) is being used, we need to switch to a new branch with this branch's name,
### so that uses of git-clone-related from the CF's own scripts to fetch do-like-javac return the current branch

cd /tmp/"$USER"/checker-framework
cf_branch_name=$(git rev-parse --abbrev-ref HEAD)
if [ ! "${dljc_branch_name}" = "${cf_branch_name}" ]; then
  git checkout -b "${dljc_branch_name}"
fi

### run the CF tests
./gradlew wpiManyTests wpiPlumeLibTests
