import argparse
import os
import sys
import imp

DEFAULT_OUTPUT_DIRECTORY = os.path.join(os.getcwd(), 'dljc-out')

# token that identifies the end of the options for do-like-javac and the beginning
# of the compilation command
CMD_MARKER = '--'

# insert here the correspondence between module name and the list of
# compiler/build-systems it handles.
# All supported commands should be listed here
MODULE_TO_COMMAND = {
    'javac': ['javac'],
    'ant': ['ant'],
    'gradle': ['gradle', 'gradlew'],
    'mvn': ['mvn']
}

CAPTURE_PACKAGE = 'capture'
LIB_FOLDER = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), os.path.pardir, 'lib')

class AbsolutePathAction(argparse.Action):
    """Convert a path from relative to absolute in the arg parser"""
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, os.path.abspath(values))

base_parser = argparse.ArgumentParser(add_help=False)
base_group = base_parser.add_argument_group('global arguments')
base_group.add_argument('-o', '--out', metavar='<directory>',
                        default=DEFAULT_OUTPUT_DIRECTORY, dest='output_directory',
                        action=AbsolutePathAction,
                        help='Set the results directory')
base_group.add_argument('-t', '--tool', metavar='<tool>',
                        action='store',default=None,
                        help='choose a tool to run. Valid tools include soot, checker, and inference.')
base_group.add_argument('-c', '--checker', metavar='<checker>',
                        action='store',default='NullnessChecker',
                        help='choose a checker to check')
base_group.add_argument('-s', '--solver', metavar='<solver>',
                        action='store',default='checkers.inference.solver.DebugSolver',
                        help='solver to use on constraints')
base_group.add_argument('-afud', '--afuOutputDir', metavar='<afud>',
                        action='store',default='afud/',
                        help='Annotation File Utilities output directory')
base_group.add_argument('-m', '--mode', metavar='<mode>',
                        action='store',default='INFER',
                        help='Modes of operation: TYPECHECK, INFER, ROUNDTRIP,ROUNDTRIP_TYPECHECK')
base_group.add_argument('-i', '--incremental', action='store_true',
                     help='''Do not delete the results directory across
                        runs''')
base_group.add_argument('--log_to_stderr', action='store_true',
                        help='''When set, all logging will go to stderr instead
                        of log file''')
base_group.add_argument('-j', '--jar', metavar='<jar>',
                        action='store',default=None,
                        help='Set the path to either prog2dfg.jar or apilearner.jar.')

def get_commands():
    """Return all commands that are supported."""
    #flatten and dedup the list of commands
    return set(sum(MODULE_TO_COMMAND.values(), []))

def get_module_name(command):
    """ Return module that is able to handle the command. None if
    there is no such module."""
    for module, commands in MODULE_TO_COMMAND.iteritems():
        if command in commands:
            return module
    return None

def split_args_to_parse():
    dd_index = \
        sys.argv.index(CMD_MARKER) if CMD_MARKER in sys.argv else len(sys.argv)

    args, cmd = sys.argv[1:dd_index], sys.argv[dd_index + 1:]
    capture_module_name = os.path.basename(cmd[0]) if len(cmd) > 0 else None
    mod_name = get_module_name(capture_module_name)
    return args, cmd, mod_name

def create_argparser(parents=[]):
    parser = argparse.ArgumentParser(
        parents=[base_parser] + parents,
        add_help=False,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    group = parser.add_argument_group(
        'supported compiler/build-system commands')

    supported_commands = ', '.join(get_commands())
    group.add_argument(
        CMD_MARKER,
        metavar='<cmd>',
        dest='nullarg',
        default=None,
        help=('Command to run the compiler/build-system. '
              'Supported build commands (run `do-like-javac.py --help -- <cmd_name>` for '
              'extra help, e.g. `do-like-javac.py --help -- ant`): ' + supported_commands),
    )
    return parser

def load_module(mod_name):
    # load the 'capture' package in lib
    pkg_info = imp.find_module(CAPTURE_PACKAGE, [LIB_FOLDER])
    imported_pkg = imp.load_module(CAPTURE_PACKAGE, *pkg_info)
    # load the requested module (e.g. make)
    mod_file, mod_path, mod_descr = \
        imp.find_module(mod_name, imported_pkg.__path__)
    try:
        return imp.load_module(
            '{pkg}.{mod}'.format(pkg=imported_pkg.__name__, mod=mod_name),
            mod_file, mod_path, mod_descr)
    finally:
        if mod_file:
            mod_file.close()

def parse_args():
    to_parse, cmd, mod_name = split_args_to_parse()
    # get the module name (if any), then load it
    imported_module = None
    if mod_name:
        imported_module = load_module(mod_name)

    # get the module's argparser and merge it with the global argparser
    module_argparser = []
    if imported_module:
        module_argparser.append(
            imported_module.create_argparser(mod_name)
        )
    global_argparser = create_argparser(module_argparser)

    args = global_argparser.parse_args(to_parse)

    if imported_module:
        return args, cmd, imported_module
    else:
        global_argparser.print_help()
        sys.exit(os.EX_OK)
