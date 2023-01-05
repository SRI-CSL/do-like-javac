# Copyright (c) 2015 - present Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the BSD style license found in the
# LICENSE_Facebook file in the root directory of this source tree. An
# additional grant of patent rights can be found in the PATENTS_Facebook file
# in the same directory.

import os
import re

from . import generic

supported_commands = ['mvn', 'mvnw']

def gen_instance(cmd, args):
    return MavenCapture(cmd, args)

class MavenCapture(generic.GenericCapture):
    def __init__(self, cmd, args):
        super(MavenCapture, self).__init__(cmd, args)
        self.build_cmd = [cmd[0], '-X', '-B'] + cmd[1:]

        # Automatically promote to mvnw if available
        if os.path.exists('mvnw'):
          self.build_cmd[0] = './mvnw'

    def get_target_jars(self, verbose_output):
        jar_pattern = '[INFO] Building jar: '
        jars = []

        for line in verbose_output:
            if jar_pattern in line:
                pos = line.index(jar_pattern) + len(jar_pattern)
                jar = line[pos:].strip()
                jars.append(jar)

        return jars

    def get_javac_commands(self, verbose_output):
        file_pattern = r'\[DEBUG\] Stale source detected: ([^ ]*\.java)'
        options_pattern = '[DEBUG] Command line options:'

        javac_commands = []
        files_to_compile = []
        options_next = False

        for line in verbose_output:
            if options_next:
                #  line has format [Debug] <space separated options>
                javac_args = line.split(' ')[1:] + files_to_compile
                javac_commands.append(javac_args)
                options_next = False
                files_to_compile = []
            elif options_pattern in line:
                #  Next line will have javac options to run
                options_next = True

            else:
                found = re.match(file_pattern, line)
                if found:
                    files_to_compile.append(found.group(1))

        return list(map(self.javac_parse, javac_commands))
