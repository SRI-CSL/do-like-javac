#!/usr/bin/env python2.7

import logging
import os
import sys
import platform
import pprint
import arg
import log
import soot
import infer
import check
import jprint
import randoop
import graphtools

def soot_tool(results,jars,args):
    soot.run_soot(results)

def checker_tool(results,jars,args):
    check.run_checker(results,args)

def inference_tool(results,jars,args):
    infer.run_inference(results,args)

def print_tool(results,jars,args):
    jprint.run_printer(results, jars)

def randoop_tool(results,jars,args):
    randoop.run_randoop(results)

def graph_tool(results,jars,args):
    graphtools.run(results,args)


def log_header():
    logging.info('Running command %s', ' '.join(sys.argv))
    logging.info('Platform: %s', platform.platform())
    logging.info('PATH=%s', os.getenv('PATH'))
    logging.info('SHELL=%s', os.getenv('SHELL'))
    logging.info('PWD=%s', os.getenv('PWD'))

def main():
    args, cmd, imported_module = arg.parse_args()
    log.configure_logging(args.output_directory, args.incremental, args.log_to_stderr)

    log_header()

    javac_commands, jars = imported_module.gen_instance(cmd).capture()
    logging.info('Results: %s', pprint.pformat(javac_commands))

    options = {'soot' : soot_tool,
               'checker' : checker_tool,
               'inference' : inference_tool,
               'print' : print_tool,
               'randoop' : randoop_tool,
               'graphtool' : graph_tool,
    }

    if args.tool:
        options[args.tool](javac_commands,jars,args)

if __name__ == '__main__':
    main()
