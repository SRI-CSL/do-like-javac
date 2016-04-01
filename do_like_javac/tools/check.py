# DEPRECATED -- WILL BE REMOVED IN FUTURE VERSION

import os
import pprint
import subprocess
import traceback
import argparse

argparser = None

def run(args, javac_commands, jars):
    # checker-framework javac.
    javacheck = os.environ['JSR308']+"/checker-framework/checker/bin/javac"
    checker_command = [javacheck, "-processor", args.checker]

    for jc in javac_commands:
        pprint.pformat(jc)
        javac_switches = jc['javac_switches']
        cp = javac_switches['classpath']
        java_files = ' '.join(jc['java_files'])
        cmd = checker_command + ["-classpath", cp, java_files]
        print ("Running %s" % cmd)
        try:
            print (subprocess.check_output(cmd, stderr=subprocess.STDOUT))
        except subprocess.CalledProcessError as e:
            print e.output
