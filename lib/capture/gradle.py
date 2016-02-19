# Copyright (c) 2015 - present Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the BSD style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.

import util
import generic

MODULE_NAME = __name__
MODULE_DESCRIPTION = '''Run analysis of code built with a command like:
gradle [options] [task]

Analysis examples:
capture_javac.py -- gradle build
capture_javac.py -- ./gradlew build'''

def gen_instance(cmd):
    return GradleCapture(cmd)

# This creates an empty argparser for the module, which provides only
# description/usage information and no arguments.
create_argparser = util.base_argparser(MODULE_DESCRIPTION, MODULE_NAME)


class GradleCapture(generic.GenericCapture):

    def __init__(self, cmd):
        self.build_cmd = [cmd[0], '--debug'] + cmd[1:]

    def get_javac_commands(self, verbose_output):
        argument_start_pattern = ' Compiler arguments: '
        results = []

        for line in verbose_output:
            if argument_start_pattern in line:
                content = line.partition(argument_start_pattern)[2].strip()
                results.append(content.split(' '))

        return map(self.javac_parse, results)
