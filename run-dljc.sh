#!/bin/bash

# This script runs the Checker Framework on each of a list of projects.

### Usage

# - Move this script to an experiment directory.
# - Make a file containing a list of git repositories, one per line.
# - Set variables in the "Configuration" section below.
# - Run the following command:
#     bash run-dljc.sh OUTDIR INLIST
#
# Where OUTDIR is a name for the experiment you're running, and
# INLIST is the file containing list of git repositories.
#
# This script works as follows:
# - Checkout each repository into OUTDIR/.
# - Use do-like-javac to build it once, then
#   replay the javac commands with checkers enabled.
# - Place a copy of the results in the directory OUTDIR-results/.


### Configuration

# JAVA_HOME must point to a Java 8 JDK.
if [ "x${JAVA_HOME}" = "x" ]; then
    JAVA_HOME=/usr/lib/jvm/java-1.8.0-openjdk
fi

# What typecheckers should be run?
CHECKERS=org.checkerframework.checker.builder.TypesafeBuilderChecker

# If you want to use a custom typechecker or typecheckers,
# define their dependencies here.
CHECKER_LIB=/homes/gws/kelloggm/image-sniping-oss/typesafe-builder-checker/build/libs/typesafe-builder-checker.jar:/homes/gws/kelloggm/.m2/repository/org/springframework/spring-expression/5.1.7.RELEASE/spring-expression-5.1.7.RELEASE.jar:/homes/gws/kelloggm/.m2/repository/org/springframework/spring-core/5.1.7.RELEASE/spring-core-5.1.7.RELEASE.jar:/homes/gws/kelloggm/.m2/repository/org/springframework/spring-jcl/5.1.7.RELEASE/spring-jcl-5.1.7.RELEASE.jar:

# Should any stub files be used?
STUBS=/homes/gws/kelloggm/image-sniping-oss/typesafe-builder-checker/stubs


### Script

# clone DLJC if it's not present
if [ ! -d do-like-javac ]; then
    git clone https://github.com/kelloggm/do-like-javac
fi

PWD=`pwd`

DLJC=${PWD}/do-like-javac/dljc

if [ "x${CHECKERFRAMEWORK}" = "x" ]; then

    if [ ! -d checker-framework ]; then
	git clone https://github.com/typetools/checker-framework
    fi
    export CHECKERFRAMEWORK=${PWD}/checker-framework
fi
    
PATH=${JAVA_HOME}/bin:${PATH}

mkdir -p $1
mkdir -p $1-results

pushd $1

for repo in `cat ../$2`; do
    
    REPO_NAME=`echo ${repo} | cut -d / -f 5`
    
    if [ ! -d ${REPO_NAME} ]; then
        git clone ${repo}
    fi

    pushd ${REPO_NAME}

    if [ -f build.gradle ]; then
	BUILD_CMD="./gradlew clean compileJava -Dorg.gradle.java.home=${JAVA_HOME}"
    elif [ -f pom.xml ]; then
	BUILD_CMD="mvn clean compile -Djava.home=${JAVA_HOME}/jre"
    else
        BUILD_CMD="not found"
    fi
    
    if [ "${BUILD_CMD}" = "not found" ]; then
        echo "no build file found for ${REPO_NAME}; not calling DLJC" > ../../$1-results/${REPO_NAME}-check.log 
    else
        ${DLJC} --lib ${CHECKER_LIB} -t checker --checker ${CHECKERS} --stubs ${STUBS} -- ${BUILD_CMD}

        cp dljc-out/check.log ../../$1-results/${REPO_NAME}-check.log
    fi
 
    popd
done

popd
