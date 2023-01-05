Extending DLJC
==================

## Supporting a new build system

Create a new Python file in `do_like_javac/capture/` named after the build system you
want to support. Start with this template:

```python
from . import generic

supported_commands = [...]

class MyCapture(generic.GenericCapture):
    def __init__(self, cmd, args):
        super(MyCapture, self).__init__(cmd, args)
        self.build_cmd = [...]

    def get_javac_commands(self, verbose_output):
        return []

    get_target_jars(self, verbose_output):
        return []

def gen_instance(cmd, args):
    return MyCapture(cmd, args)
```

Where supported\_commands is a list of commands that might be used to invoke the
build system (e.g. "gradle", "gradlew", "ant", "maven").

For the constructor, cmd is a sys.argv style list containing the build command
the user supplied at the command line. For example, if they wrote

    dljc -t print -- mybuildsystem -arg1 -arg2 -arg3

then cmd would contain `['mybuildsystem', '-arg1', '-arg2', '-arg3']`. You
should set self.build_cmd to be a version of that command that invokes the build
system with flags that give you the verbose output you'll need to parse the
javac commands from.

`args` is the argparse structure that dljc stores its own arguments in. You can
find more details in `do_like_javac/arg.py`.

Your job now is to implement `get_javac_commands` and optionally
`get_target_jars`. verbose\_output contains a list of lines of output from
running the build system. If your build system outputs entire javac commands
on a single line, or if you can reconstitute the commands in their entirety,
then there's a convenience method called `javac_parse` defined in the
superclass, which expects a list of words in the command and produces the
output you need.

If not, the ouput format is a list of javac command dicts, which are of the
form:

```python
{
    'java_files': ['Foo.java', 'Bar.java', ...],
    'javac_switches': {
        # Switches have the - prefix removed.
        # Value is either the argument given to the switch,
        # or True for no-argument flags.
        'classpath': ...,
        ...
    }
}
```

`get_target_jars` returns a list of paths to jar files output by the build.

Finally, add your new module to the `capture_modules` list at the top of
`do_like_javac/capture/__init__.py`.

## Adding a new analysis tool

Create a new Python file in `do_like_javac/tools/` named after the tool you
want to add. Use this template:

```python
argparser = None

def run(args, javac_commands, jars):
    print("My tool results.")
```

`args` is the argparse structure created by DLJC. `argparser` is where you can
plug in additional command line options you'd like to be available for your
tool. You can see an example in `do_like_javac/tools/infer.py`.

`javac_commands` and `jars` are the structures discussed above, consisting of
the javac command used to build the project and the jar files generated (if
that information is available).

After augmenting `run()` to do what you want, add your tool to the `TOOLS`
dictionary at the top of `do_like_javac/tools/__init__.py`, along with a
`from . import mytoolname` statement.
