#!/bin/bash

# usage:
# - Move this script to an experiment directory.
# - Then create a list of git reposities, and place it in
#   the file INLIST, one repository per line
# - Then run the following command:
#   > bash run-dljc.sh OUTDIR INLIST
#
# Where OUTDIR is a name for the experiment you're running, and
# INLIST is the list of git repositories.
#
# This script will:
# - Checkout each repository into OUTDIR/.
# - Attempt to build it with do-like-javac.
# - If it can be built, attempt to replay the javac commands
#   with checkers enabled.
# - Place a copy of the results in the directory OUTDIR-results/.
#
# Configuration:
# - Ensure that JAVA_HOME points to a java 8 JDK,
#   or set the JAVA_HOME variable below.
# - Configure the checkers to run using the CHECKERS variable below.
# - Create a list of the dependencies of any custom checkers you
#   want to use, and set the CHECKER_LIB variable below accordingly.
# - Set the STUBS variable below if you want to use any stub files.

# requirements:
# JAVA_HOME must point to a Java 8 JDK for this script to work
if [ "x${JAVA_HOME}" = "x" ]; then
    JAVA_HOME=/usr/lib/jvm/java-1.8.0-openjdk
fi

# what typecheckers should be run?
CHECKERS=org.checkerframework.checker.builder.TypesafeBuilderChecker

# if you want to use a custom typechecker or typecheckers,
# define their dependencies here
CHECKER_LIB=/homes/gws/kelloggm/image-sniping-oss/typesafe-builder-checker/build/libs/typesafe-builder-checker.jar:/homes/gws/kelloggm/.m2/repository/org/springframework/spring-expression/5.1.7.RELEASE/spring-expression-5.1.7.RELEASE.jar:/homes/gws/kelloggm/.m2/repository/org/springframework/spring-core/5.1.7.RELEASE/spring-core-5.1.7.RELEASE.jar:/homes/gws/kelloggm/.m2/repository/org/springframework/spring-jcl/5.1.7.RELEASE/spring-jcl-5.1.7.RELEASE.jar:

# should any stub files be used?
STUBS=/homes/gws/kelloggm/image-sniping-oss/typesafe-builder-checker/stubs

# script:

# clone DLJC if its not present
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

mkdir $1 || true
mkdir $1-results || true

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
