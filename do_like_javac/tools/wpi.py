import shlex
import sys
from filecmp import dircmp

import common
import os
import pprint
import shutil
import tempfile
import subprocess32 as subprocess

# re-use existing CF build logic
import check

argparser = None

banned_options = ["nowarn", "classpath", "processorpath", "processor", "Xmaxerrs", "Xmaxwarns"]

def run(args, javac_commands, jars):
    # checker-framework javac.
    javacheck = os.environ['CHECKERFRAMEWORK']+"/checker/bin/javac"
    checker_command = [javacheck, "-Ainfer=stubs", "-AmergeStubsWithSource", "-Xmaxerrs", "10000", "-Xmaxwarns", "10000"]
    if args.checker is not None:
        processorArg = ["-processor", args.checker]
    else:
        # checker should run via auto-discovery
        processorArg = []

    checker_command += check.getArgumentsByVersion(args.jdkVersion)

    if args.cleanCmd is None:
        print "to run whole-program inference, you must provide a clean command using the --cleanCmd argument"
        sys.exit(1)
    else:
        cleanCmd = shlex.split(args.cleanCmd)

    for jc in javac_commands:

        wpiDir = os.path.join(os.getcwd(), 'build/whole-program-inference')
        # if there is already a WPI directory, delete it and start over
        if os.path.isdir(wpiDir):
            shutil.rmtree(wpiDir)

        iteration = 0
        diffResult = 1
        stubDirs = []
        while diffResult != 0:

            # first, clean the project before each CF run
            common.run_cmd(cleanCmd, args, 'wpi')

            iterationStubs = ':'.join(stubDirs)
            stubArg = None

            if args.stubs:
                stubArg = "-Astubs=" + str(args.stubs) + ":" + iterationStubs
            elif iterationStubs != "":
                stubArg = "-Astubs=" + iterationStubs

            if stubArg is not None:
                iterationCheckerCmd = checker_command + [stubArg]
            else:
                iterationCheckerCmd = checker_command

            pprint.pformat(jc)
            javac_switches = jc['javac_switches']
            # include processor path in the class path if it is present
            pp = ''
            if javac_switches.has_key('processorpath'):
                pp = javac_switches['processorpath'] + ':'
            cp = javac_switches['classpath']
            if args.quals:
                 cp += args.quals + ':'
            if args.lib_dir:
                cp += pp + args.lib_dir + ':'
            if javac_switches.has_key('processor') and len(processorArg) == 2:
                processorArg[1] += "," + javac_switches['processor']
            java_files = jc['java_files']
            other_args = []
            for k, v in javac_switches.items():
                if not k in banned_options:
                    if v is None or v is not False:
                        other_args.append("-" + k)
                    if v is not None and v is not True:
                        other_args.append(str(v))
            cmd = iterationCheckerCmd + ["-classpath", cp] + processorArg + other_args + java_files
            common.run_cmd(cmd, args, 'wpi')

            # process outputs
            # move the old wpi files, add them to stub path
            previousIterationDir = tempfile.mkdtemp(suffix="iteration" + str(iteration))
            stubs = os.listdir(wpiDir)

            for stub in stubs:
                shutil.move(os.path.join(wpiDir, stub), previousIterationDir)

            stubDirs.append(previousIterationDir)

            if len(stubDirs) > 1:
                dcmp = dircmp(stubDirs[-1], stubDirs[-2])
                diffResult = len(dcmp.diff_files)
