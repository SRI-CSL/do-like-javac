# Copyright (c) 2013 - present Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the BSD style license found in the
# LICENSE_Facebook file in the root directory of this source tree. An
# additional grant of patent rights can be found in the PATENTS_Facebook file
# in the same directory.

import logging
import os
import platform
import sys

FORMAT = '[%(levelname)s] %(message)s'
LOG_FILE = 'toplevel.log'

def create_results_dir(results_dir):
    try:
        os.mkdir(results_dir)
    except OSError:
        pass

def configure_logging(output_directory, log_to_stderr):
    create_results_dir(output_directory)

    if log_to_stderr:
        logging.basicConfig(level=logging.INFO, format=FORMAT)
    else:
        logging.basicConfig(level=logging.INFO,
                            format=FORMAT,
                            filename=os.path.join(output_directory, LOG_FILE),
                            filemode='w')

def log_header():
    logging.info('Running command %s', ' '.join(sys.argv))
    logging.info('Platform: %s', platform.platform())
    logging.info('PATH=%s', os.getenv('PATH'))
    logging.info('SHELL=%s', os.getenv('SHELL'))
    logging.info('PWD=%s', os.getenv('PWD'))

def info(*args):
    logging.info(*args)

# vim: set sw=4 ts=4 et:
