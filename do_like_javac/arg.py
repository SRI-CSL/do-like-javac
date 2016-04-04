import argparse
import os
import sys

import tools
import capture

DEFAULT_OUTPUT_DIRECTORY = os.path.join(os.getcwd(), 'dljc-out')

# token that identifies the end of the options for do-like-javac and the beginning
# of the compilation command
CMD_MARKER = '--'

class AbsolutePathAction(argparse.Action):
    """Convert a path from relative to absolute in the arg parser"""
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, os.path.abspath(values))

base_parser = argparse.ArgumentParser(add_help=False)
base_group = base_parser.add_argument_group('global arguments')
base_group.add_argument('-o', '--out', metavar='<directory>',
                        default=DEFAULT_OUTPUT_DIRECTORY, dest='output_directory',
                        action=AbsolutePathAction,
                        help='The directory to log results.')
base_group.add_argument('--log_to_stderr', action='store_true',
                        help='''Redirect log messages to stderr instead of log file''')
base_group.add_argument('-t', '--tool', metavar='<tool>',
                        action='store',default=None,
                        help='A comma separated list of tools to run. Valid tools: ' + ', '.join(tools.TOOLS))

# base_group.add_argument('-c', '--checker', metavar='<checker>',
#                         action='store',default='NullnessChecker',
#                         help='A checker to check (for checker/inference tools)')

def split_args_to_parse():
    split_index = len(sys.argv)
    if CMD_MARKER in sys.argv:
        split_index = sys.argv.index(CMD_MARKER)

    args, cmd = sys.argv[1:split_index], sys.argv[split_index + 1:]

    command_name = os.path.basename(cmd[0]) if len(cmd) > 0 else None
    capturer = capture.get_capturer(command_name)
    return args, cmd, capturer

def create_argparser():
    parser = argparse.ArgumentParser(
        parents=[base_parser] + tools.parsers(),
        add_help=False,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    group = parser.add_argument_group(
        'supported compiler/build-system commands')

    supported_commands = ', '.join(capture.supported_commands())
    group.add_argument(
        CMD_MARKER,
        metavar='<cmd>',
        dest='nullarg',
        default=None,
        help=('Command to run the compiler/build-system. '
              'Supported build commands: ' + supported_commands),
    )

    return parser

def parse_args():
    to_parse, cmd, capturer = split_args_to_parse()

    global_argparser = create_argparser()

    args = global_argparser.parse_args(to_parse)

    if capturer:
        return args, cmd, capturer
    else:
        global_argparser.print_help()
        sys.exit(os.EX_OK)
