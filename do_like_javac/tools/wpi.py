import sys

import common
import os
import pprint
import shutil
import tempfile
import subprocess32 as subprocess

argparser = None

def run(args, javac_commands, jars):
    # checker-framework javac.
    javacheck = os.environ['CHECKERFRAMEWORK']+"/checker/bin/javac"
    if args.checker is not None:
        checker_command = [javacheck, "-processor", args.checker, "-Ainfer=stubs", "-AmergeStubsWithSource"]
    else:
        # checker should run via auto-discovery
        checker_command = [javacheck, "-Ainfer=stubs", "-AmergeStubsWithSource"]

    for jc in javac_commands:

        wpiDir = os.path.join(os.getcwd(), 'build/whole-program-inference')
        # if there is already a WPI directory, delete it and start over
        if os.path.isdir(wpiDir):
            shutil.rmtree(wpiDir)

        iteration = 0
        diffResult = 1
        stubDirs = []
        while diffResult != 0:

            if os.path.isdir(wpiDir):
                # move the old wpi files, add them to stub path
                previousIterationDir = tempfile.mkdtemp(suffix="iteration" + str(iteration))
                stubs = os.listdir(wpiDir)

                for stub in stubs:
                    shutil.move(os.path.join(wpiDir, stub), previousIterationDir)

                stubDirs.append(previousIterationDir)

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
            if args.lib_dir:
                cp = cp + ':' + pp + args.lib_dir + ':'
            java_files = jc['java_files']
            cmd = iterationCheckerCmd + ["-classpath", cp] + java_files
            common.run_cmd(cmd, args, 'wpi')

            if len(stubDirs) != 0:
                if args and args.verbose and args.log_to_stderr:
                    out = sys.stderr
                else:
                    out_file = os.path.join(args.output_directory,  "wpi.log")
                    out = open(out_file, 'a')

                diffResult = subprocess.run(["diff", "-qr", wpiDir, stubDirs[-1]], stdout=out).returncode