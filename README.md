do-like-javac
=============

`do-like-javac` (or dljc for short) is a tool for monitoring the build process of
a Java project and recording information about what parameters were passed to `javac`
for the purpose of later analysis. It can also automate the running of various
analysis tools, including:

* [Randoop](https://randoop.github.io/randoop/)
* [Bixie](http://sri-csl.github.io/bixie/)
* [Checker Framework](http://types.cs.washington.edu/checker-framework/)

`do-like-javac` supports projects built with:

* Apache Ant
* Apache Maven
* Gradle
* Manual invocation of `javac`

If you have a project that builds through Eclipse that you want to analyze,
Eclipse can generate an Ant-compatible `build.xml` file by right-clicking the
project, selecting "Export" and choosing the "Ant Buildfiles" option.

Dependencies
============

* Python 3
* The analysis tool(s) you want to run.
* Any build dependencies of the project you're analyzing.

`do-like-javac` was built and tested on Mac OS X and GNU/Linux. It may also
work on Microsoft Windows, but we provide no support.

Installation
============

    git clone https://github.com/SRI-CSL/do-like-javac.git

Then symlink the `dljc` executable to somewhere in your $PATH, e.g.

    ln -s /path/to/dljc $HOME/bin/dljc

Running
=======

First, make sure your project is in a clean state (e.g. via `ant clean`,
`mvn clean`, etc.). Since `do-like-javac` monitors the build process and build
tools skip already-built files, if you run `dljc` on an already-built project,
you won't get any results.

Next, invoke `dljc` from the directory of the project you want to analyze:

    dljc -o logs -- ant build

Where "ant build" is replaced by whatever command builds your project. Output
will be emitted to logs/toplevel.log

You may also run one or more checking tools on the discovered java files, by
invoking with the -t option and a comma separated list of tools to use (e.g.
"-t print", "-t randoop" or "-t print,randoop").

If you're running checking tools, there are a couple more flags that may be
helpful. `--quiet` suppresses output from tools, and `--timeout <seconds>`
kills any tool subcommand that runs longer than `<seconds>`.

Extending
===========

Instructions for adding support for new tools or build systems to DLJC can be
found in [Extending.md](./Extending.md).

Caching
=======

`do-like-javac` can only extract data from a full compile of a project. That means
if you want to re-run it with new arguments or different analysis tools, you will
have to clean and fully re-compile the project. To save time and shortcut this
process, we save a cache of the results in the output directory. If you want `dljc`
to use this cache, simply add the `--cache` flag and the cache (if available) will
be used instead of recompiling the project.

**IMPORTANT NOTE**: We don't do any sort of cache invalidation or freshness checking.
If you add new files to your project and want `dljc` to pick up on them, you will have
to do a full clean and run `dljc` without the `--cache` flag.

Supported Tools
===============

Print
-----

The print tool (`dljc -t print`) will pretty-print the detected `javac` commands, as well as any generated JAR files, and their entry points if applicable.

Bixie
-----

The Bixie tool will run your project through [Bixie](http://sri-csl.github.io/bixie/). You will need to provide a library directory containing bixie.jar using the `--lib` option.

    dljc --lib path/to/libs/ -t bixie -- mvn compile

Dyntrace
---------

The Dyntrace tool will run your project through Randoop to generate tests, then run those tests with Daikon/Chicory to generate likely invariants. You will need to provide a library directory with the following jars using the `--lib` option:

* randoop.jar
* junit-4.12.jar
* hamcrest-core-1.3.jar

You will also need Daikon built and installed somewhere, with the environment variable `DAIKONDIR` pointing to your installation.

    dljc --lib path/to/libs/ -t dyntrace -- mvn compile


LICENSE
=======

Parts of the code in this project were taken from the Facebook Infer project.
Files containing such code have Facebook copyright notices at the top and are
licensed under the terms laid out in LICENSE_Facebook.

The rest of the project is licensed under the BSD license under the terms laid
out in LICENSE.
