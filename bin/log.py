# Copyright (c) 2013 - present Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the BSD style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.

import os
import shutil
import logging

FORMAT = '[%(levelname)s] %(message)s'
LOG_FILE = 'toplevel.log'

def remove_output_directory(output_directory):
    # it is safe to ignore errors here because recreating the
    # output_directory will fail later
    shutil.rmtree(output_directory, True)

def create_results_dir(results_dir):
    try:
        os.mkdir(results_dir)
    except OSError:
        pass

def configure_logging(output_directory, incremental, log_to_stderr):
    #if not incremental:
    #    remove_output_directory(output_directory)

    create_results_dir(output_directory)

    if log_to_stderr:
        logging.basicConfig(level=logging.INFO, format=FORMAT)
    else:
        logging.basicConfig(level=logging.INFO,
                            format=FORMAT,
                            filename=os.path.join(output_directory, LOG_FILE),
                            filemode='w')

# vim: set sw=4 ts=4 et:
