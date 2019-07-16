# DEPRECATED -- WILL BE REMOVED IN FUTURE VERSION

import common
import os
import pprint

argparser = None

def run(args, javac_commands, jars):
    # checker-framework javac.
    javacheck = os.environ['CHECKERFRAMEWORK']+"/checker/bin/javac"
    if args.checker is not None:
        checker_command = [javacheck, "-processor", args.checker, "-Astubs=" + str(args.stubs)]
    else:
        # checker should run via auto-discovery
        checker_command = [javacheck, "-Astubs=" + str(args.stubs)]

    for jc in javac_commands:
        pprint.pformat(jc)
        javac_switches = jc['javac_switches']
        # include processor path in the class path if it is present
        pp = ''
        if javac_switches.has_key('processorpath'):
            pp = javac_switches['processorpath'] + ':'
        cp = javac_switches['classpath']
        cp = cp + ':' + pp + args.lib_dir + ':'
        java_files = jc['java_files']
        cmd = checker_command + ["-classpath", cp] + java_files
        common.run_cmd(cmd, args, 'check')
