# Copyright (c) 2013 - present Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the BSD style license found in the
# LICENSE_Facebook file in the root directory of this source tree. An
# additional grant of patent rights can be found in the PATENTS_Facebook file
# in the same directory.

import argparse
import os
import sys

from . import capture, tools

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

base_group.add_argument('--timeout', metavar='<seconds>',
                        action='store', default=None,
                        type=int,
                        help='The maximum time to run any subcommand.')

base_group.add_argument('--guess', action='store_true', dest='guess_source',
                        help="Guess source files if not present in build output.")

base_group.add_argument('--quiet', action='store_false', dest='verbose',
                        help="Suppress output from subcommands.")

base_group.add_argument('--cache', action='store_true',
                        help='''Use the dljc cache (if available)''')

base_group.add_argument('-c', '--checker', metavar='<checker>',
                        action='store', 
                        # do not run the NullnessChecker by default
                        # default='NullnessChecker',
                        help='A checker to check (for checker/inference tools)')

base_group.add_argument('--stubs', metavar='<stubs>',
                        action=AbsolutePathAction,
                        help='Location of stub files to use for the Checker Framework')

base_group.add_argument('--ajava', metavar='<ajava>',
                        action=AbsolutePathAction,
                        help='Location of ajava files to use for the Checker Framework')

base_group.add_argument('-l', '--lib', metavar='<lib_dir>',
                        action='store',dest='lib_dir',
                        help='Library directory with JARs for tools that need them.')

base_group.add_argument('--jdkVersion', metavar='<jdkVersion>',
                        action='store',
                        help='Version of the JDK to use with the Checker Framework.')

base_group.add_argument('--quals', metavar='<quals>',
                        action='store',
                        help='Path to custom annotations to put on the classpath when using the Checker Framework.')

base_group.add_argument('--extraJavacArgs', metavar='<extraJavacArgs>',
                        action='store',
                        help='List of extra arguments to pass to javac when running a Checker Framework checker. Use this for '
                             'arguments that are only needed when running a checker, such as -AassumeSideEffectFree.')

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
