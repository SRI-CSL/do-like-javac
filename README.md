do-like-javac
=============

`do-like-javac` (or dljc for short) is a tool for monitoring the build process of
a Java project and recording information about what parameters were passed to `javac`
for the purpose of later analysis. It can also automate the running of various
analysis tools, including:

* [Randoop](https://randoop.github.io/randoop/)
* [Checker Framework](http://types.cs.washington.edu/checker-framework/)
* [Soot](https://sable.github.io/soot/)

`do-like-javac` supports projects built with:

* Apache Ant
* Apache Maven
* Gradle
* Manual invocation of `javac`

Dependencies
============

* Python 2.7

That's it. No other external dependencies for the core `do-like-javac` scripts.

Of course, you will also need to have installed:

* The analysis tool(s) you want to run. 
* Any build dependencies of the project you're analyzing.

`do-like-javac` was built and tested on Mac OS X and GNU/Linux. It probably also
works on Microsoft Windows, but the method of invocation is probably different and
we provide no support.

Installation
============

    git clone https://github.com/SRI-CSL/do-like-javac.git

Then symlink the `dljc` executable to somewhere in your $PATH, e.g.

    ln -s /path/to/dljc $HOME/bin/dljc

Running
=======

Invoke `dljc` from the directory of the project you want to analyze:

    dljc -o logs -- ant build

Where "ant build" is replaced by whatever command builds your project. Output
will be emitted to logs/toplevel.log

You may also run one or more checking tools on the discovered java files, by
invoking with the -t option and a comma separated list of tools to use (e.g.
"-t print", "-t randoop" or "-t print,randoop").

LICENSE
=======

Parts of the code in this directory were taken from the Facebook Infer project.
Its license is available at

  https://github.com/facebook/infer/blob/master/LICENSE
