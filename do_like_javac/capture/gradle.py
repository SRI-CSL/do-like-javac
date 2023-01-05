# Copyright (c) 2015 - present Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the BSD style license found in the
# LICENSE_Facebook file in the root directory of this source tree. An
# additional grant of patent rights can be found in the PATENTS_Facebook file
# in the same directory.

import os

from . import generic

supported_commands = ['gradle', 'gradlew']

def gen_instance(cmd, args):
    return GradleCapture(cmd, args)

class GradleCapture(generic.GenericCapture):
    def __init__(self, cmd, args):
        super(GradleCapture, self).__init__(cmd, args)
        self.build_cmd = [cmd[0], '--debug'] + cmd[1:]

        # Automatically promote to gradlew if available
        if os.path.exists('gradlew'):
          self.build_cmd[0] = './gradlew'

    def get_javac_commands(self, verbose_output):
        argument_start_pattern = ' Compiler arguments: '
        results = []

        for line in verbose_output:
            if argument_start_pattern in line:
                content = line.partition(argument_start_pattern)[2].strip()
                results.append(content.split(' '))

        return list(map(self.javac_parse, results))
