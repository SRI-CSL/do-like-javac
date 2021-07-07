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

### Clone the CF. If there is a branch with the same name as this branch, git-clone-related will check out that branch.
rm -rf /tmp/"$USER"/checker-framework
/tmp/"$USER"/plume-scripts/git-clone-related typetools checker-framework /tmp/"$USER"/checker-framework
export CHECKERFRAMEWORK=/tmp/"$USER"/checker-framework

export DLJC=$(pwd)/dljc

cd /tmp/"$USER"/checker-framework

### run the CF tests
./gradlew wpiManyTest wpiPlumeLibTest
