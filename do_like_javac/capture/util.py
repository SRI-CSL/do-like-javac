#!/usr/bin/env python

# Copyright (c) 2015 - present Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the BSD style license found in the
# LICENSE_Facebook file in the root directory of this source tree. An
# additional grant of patent rights can be found in the PATENTS_Facebook file
# in the same directory.

import do_like_javac.log
import os
import subprocess
import traceback

def get_build_output(build_cmd):
    #  TODO make it return generator to be able to handle large builds
    proc = subprocess.Popen(build_cmd, stdout=subprocess.PIPE, stderr=open(os.devnull, 'w'))
    (verbose_out_chars, _) = proc.communicate()
    return verbose_out_chars.split('\n')

def run_cmd_ignore_fail(cmd):
    try:
        return subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    except:
        return 'calling {cmd} failed\n{trace}'.format(
            cmd=' '.join(cmd),
            trace=traceback.format_exc())

def log_java_version():
    java_version = run_cmd_ignore_fail(['java', '-version'])
    javac_version = run_cmd_ignore_fail(['javac', '-version'])
    log.info("java versions:\n%s%s", java_version, javac_version)
