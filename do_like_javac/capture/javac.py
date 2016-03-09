# Copyright (c) 2015 - present Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the BSD style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.

import util
import generic

supported_commands = ['javac']

def gen_instance(cmd):
    return JavaCapture(cmd)

class JavaCapture(generic.GenericCapture):

    def __init__(self, cmd):
        self.build_cmd = cmd
        self.cmd = cmd[1:]

    def get_javac_commands(self, verbose_output):
        return map(self.javac_parse, [self.cmd])
