# Copyright (c) 2015 - present Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the BSD style license found in the
# LICENSE_Facebook file in the root directory of this source tree. An
# additional grant of patent rights can be found in the PATENTS_Facebook file
# in the same directory.

from . import generic

supported_commands = ['javac']

def gen_instance(cmd, args):
    return JavaCapture(cmd, args)

class JavaCapture(generic.GenericCapture):
    def __init__(self, cmd, args):
        super(JavaCapture, self).__init__(cmd, args)
        self.build_cmd = cmd
        self.cmd = cmd[1:]

    def get_javac_commands(self, verbose_output):
        return list(map(self.javac_parse, [self.cmd]))
