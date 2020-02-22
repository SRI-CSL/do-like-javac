#!/bin/bash

# This script runs the Checker Framework on each of a list of projects.

### Usage

# - Move this script to an experiment directory.
# - Make a file containing a list of git repositories, one per line. Repositories must be of the form: https://github.com/username/repository - the script is reliant on the number of slashes, so excluding https:// is an error.
# - Ensure that your JAVA_HOME variable points to a Java 8 JDK
# - Ensure that your CHECKERFRAMEWORK variable points to a built copy of the Checker Framework
# - Then run a command like the following (replacing the example arguments with your own):
#   > bash run-dljc.sh -o outdir -i describe-images-list -c org.checkerframework.checker.builder.TypesafeBuilderChecker -l /homes/gws/kelloggm/image-sniping-oss/typesafe-builder-checker/build/libs/typesafe-builder-checker.jar:/homes/gws/kelloggm/.m2/repository/org/springframework/spring-expression/5.1.7.RELEASE/spring-expression-5.1.7.RELEASE.jar:/homes/gws/kelloggm/.m2/repository/org/springframework/spring-core/5.1.7.RELEASE/spring-core-5.1.7.RELEASE.jar:/homes/gws/kelloggm/.m2/repository/org/springframework/spring-jcl/5.1.7.RELEASE/spring-jcl-5.1.7.RELEASE.jar: -s /homes/gws/kelloggm/image-sniping-oss/typesafe-builder-checker/stubs
#
# The meaning of each required argument is:
#
# -o outdir : run the experiment in the ./outdir directory, and place the
#             results in the ./outdir-results directory. Both will be created
#             if they do not exist.
#
# -i infile : read the list of repositories to use from the file $infile. Each
#             line should contain the (https) url of the git repository on
#             GitHub and the commit hash to use, separated by spaces. If the
#             repository's owner is you (see -u flag), then each line owned by
#             you must be followed by the original github repository.
#
# -c checkers : a comma-separated list of typecheckers to run
#
# The meaning of each optional argument is:
#
# -l lib : a colon-separated list of jar files which should be added to the
#          java classpath when doing typechecking. Use this for the dependencies
#          of any custom typecheckers.
#
# -q quals : a colon-separated list of the jar files containing annotations used
#            by custom checkers
#
# -s stubs : a colon-separated list of stub files
#
# -u user : the GitHub user to consider the "owner" for repositories that have
#           been forked and modified. These repositories must have a third entry
#           in the infile indicating their origin. Default is "kelloggm".
#

while getopts "c:l:s:o:i:q:w:" opt; do
  case $opt in
    c) CHECKERS="$OPTARG"
       ;;
    l) CHECKER_LIB="$OPTARG"
       ;;
    q) QUALS="$OPTARG"
       ;;
    s) STUBS="$OPTARG"
       ;;
    o) OUTDIR="$OPTARG"
       ;;
    i) INLIST="$OPTARG"
       ;;
    u) USER="$OPTARG"
       ;;
    \?) echo "Invalid option -$OPTARG" >&2
    ;;
  esac
done

# check required arguments and environment variables:

# JAVA_HOME must point to a Java 8 JDK for this script to work
if [ "x${JAVA_HOME}" = "x" ]; then
    echo "JAVA_HOME must be set to a Java 8 JDK for this script to succeed"
    exit 1
fi


if [ "x${CHECKERFRAMEWORK}" = "x" ]; then
    echo "CHECKERFRAMEWORK must be set to the base directory of a pre-built Checker Framework for this script to succeed. Please checkout github.com/typetools/checker-framework and follow the build instructions there"
    exit 2
fi

if [ "x${OUTDIR}" = "x" ]; then
    echo "you must specify an output directory using the -o argument"
    exit 3
fi

if [ "x${INLIST}" = "x" ]; then
    echo "you must specify an input file using the -i argument"
    exit 4
fi

if [ "x${USER}" = "x" ]; then
    USER=kelloggm
fi

### Script

# clone DLJC if it's not present
if [ ! -d do-like-javac ]; then
    git clone https://github.com/kelloggm/do-like-javac
fi

PWD=`pwd`

DLJC=${PWD}/do-like-javac/dljc
    
PATH=${JAVA_HOME}/bin:${PATH}

mkdir ${OUTDIR} || true
mkdir ${OUTDIR}-results || true

pushd ${OUTDIR}

while IFS= read -r line
do    
    REPOHASH=${line}
    REPO=`echo ${REPOHASH} | awk '{print $1}'`
    HASH=`echo ${REPOHASH} | awk '{print $2}'`

    REPO_NAME=`echo ${REPO} | cut -d / -f 5`
    
    if [ ! -d ${REPO_NAME} ]; then
        git clone ${REPO}
    else
        rm -rf ${REPO_NAME}/dljc-out
    fi

    pushd ${REPO_NAME}

    git checkout ${HASH}

    OWNER=`echo ${REPO} | cut -d / -f 4`

    if [ "${OWNER}" = "${USER}" ]; then
        ORIGIN=`echo ${REPOHASH} | awk '{print $3}'`
        git remote add unannotated ${ORIGIN}
    fi

    if [ -f build.gradle ]; then
	BUILD_CMD="./gradlew clean compileJava -Dorg.gradle.java.home=${JAVA_HOME}"
    elif [ -f pom.xml ]; then
	BUILD_CMD="mvn clean compile -Djava.home=${JAVA_HOME}/jre"
    else
        BUILD_CMD="not found"
    fi
    
    if [ "${BUILD_CMD}" = "not found" ]; then
        echo "no build file found for ${REPO_NAME}; not calling DLJC" > ../../${OUTDIR}-results/${REPO_NAME}-check.log 
    else
        DLJC_CMD="${DLJC} -t checker"
        if [ ! "x${CHECKERS}" = "x" ]; then
	    TMP="${DLJC_CMD} --checker ${CHECKERS}"
            DLJC_CMD="${TMP}"
        fi
	if [ ! "x${CHECKER_LIB}" = "x" ]; then
	    TMP="${DLJC_CMD} --lib ${CHECKER_LIB}"
	    DLJC_CMD="${TMP}"
	fi

	if [ ! "x${STUBS}" = "x" ]; then
	    TMP="${DLJC_CMD} --stubs ${STUBS}"
	    DLJC_CMD="${TMP}"
	fi

	if [ ! "x${QUALS}" = "x" ]; then
	    TMP="${DLJC_CMD} --quals ${QUALS}"
	    DLJC_CMD="${TMP}"
	fi

        TMP="${DLJC_CMD} -- ${BUILD_CMD}"
        DLJC_CMD="${TMP}"

	${DLJC_CMD}
        cp dljc-out/check.log ../../${OUTDIR}-results/${REPO_NAME}-check.log
    fi
 
    popd
done < ../${INLIST}

popd
