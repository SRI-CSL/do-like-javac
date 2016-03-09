Running
=======

To run, make a symlink to bin/dljc somewhere on your PATH and invoke from the
directory of the project you want to analyze:

    dljc -o logs -- ant build

Where "ant build" is replaced by whatever command builds your project. Output
will be emitted to logs/toplevel.log

You may also run a checking tool on the discovered java files, by invoking with
the -t option and a tool to use (e.g. "-t print", "-t inference" or "-t checker").

LICENSE
=======

Parts of the code in this directory were taken from the Facebook Infer project.
Its license is available at

  https://github.com/facebook/infer/blob/master/LICENSE
