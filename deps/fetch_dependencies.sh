#!/usr/bin/env bash

# Fail the whole script if any command fails
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
pushd ${DIR} &> /dev/null

# Libraries
mkdir -p libs
pushd libs &> /dev/null

JARS=(
    "https://github.com/aas-integration/prog2dfg/releases/download/v0.1/prog2dfg.jar"
    "https://github.com/junit-team/junit/releases/download/r4.12/junit-4.12.jar"
    "http://search.maven.org/remotecontent?filepath=org/hamcrest/hamcrest-core/1.3/hamcrest-core-1.3.jar"
    "https://github.com/aas-integration/clusterer/releases/download/v0.6/clusterer.jar"
    "https://github.com/SRI-CSL/bixie/releases/download/0.3/bixie.jar"
)

for jar in "${JARS[@]}"
do
    base=$(basename ${jar})
    echo Fetching ${base}

    if curl -fLo ${base} ${jar} &> /dev/null; then
      :
    else
      echo Fetching ${base} failed.
      exit 1;
    fi
done

# Fetch the current version of randoop jars
RANDOOPBASEURL="https://github.com/randoop/randoop/releases/download"
RANDOOPVERSION=`curl --silent "https://api.github.com/repos/randoop/randoop/releases/latest"|grep '"tag_name"'|sed -E 's/.*"v([^"]+)".*/\1/'`
jar=$RANDOOPBASEURL/v$RANDOOPVERSION/randoop-all-$RANDOOPVERSION.jar
    base=$(basename ${jar})
    echo Fetching ${base}

    if curl -fLo ${base} ${jar} &> /dev/null; then
      # Rename randoop's release-specific-name to just randoop.jar
      mv ${base} "randoop.jar"
    else
      echo Fetching ${base} failed.
      exit 1;
    fi

jar=$RANDOOPBASEURL/v$RANDOOPVERSION/replacecall-$RANDOOPVERSION.jar
    base=$(basename ${jar})
    echo Fetching ${base}

    if curl -fLo ${base} ${jar} &> /dev/null; then
      # Rename replacecall's release-specific-name to just replacecall.jar
      mv ${base} "replacecall.jar"
    else
      echo Fetching ${base} failed.
      exit 1;
    fi
# extract the default replacements file
jar -xf replacecall.jar default-replacements.txt

popd &> /dev/null # Exit libs

# Tools
mkdir -p tools
pushd tools &> /dev/null

# Fetch Daikon if not using external
if [[ -z "${DAIKONDIR}" ]]; then
    DAIKONBASEURL="http://plse.cs.washington.edu/daikon"
    DAIKONVERSION=`curl --fail -s $DAIKONBASEURL/download/doc/VERSION | xargs echo -n`
    DAIKON_SRC=$DAIKONBASEURL/download/daikon-$DAIKONVERSION.tar.gz
    DAIKON_SRC_FILE=$(basename ${DAIKON_SRC})

    if [ ! -e $DAIKON_SRC_FILE ]; then
    rm -rf daikon-src

    if curl -fLo $DAIKON_SRC_FILE $DAIKON_SRC; then
        bash ../build_daikon.sh `pwd`/$DAIKON_SRC_FILE
        cp daikon-src/daikon.jar ../libs/daikon.jar
    else
        echo "Fetching $DAIKON_SRC failed."
        exit 1;
    fi

    else
        echo "Daikon already up to date."
    fi
fi

popd &> /dev/null # Exit tools

popd &> /dev/null # Exit integration-test
