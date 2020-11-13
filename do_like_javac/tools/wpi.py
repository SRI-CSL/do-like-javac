import shlex
import sys
from filecmp import dircmp

import common
import os
import pprint
import shutil
import tempfile
from distutils import dir_util
import subprocess32 as subprocess

# re-use existing CF build logic
import check

argparser = None

banned_options = ("classpath", "release",
                  "nowarn", "Xmaxerrs", "Xmaxwarns", "Werror",
                  "processorpath", "processor", "proc:none",
                  "XepDisableAllChecks", "Xplugin:ErrorProne")
banned_options_prefixes = ("Xep:", "XepExcludedPaths:")

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

    for jc in javac_commands:

        # something searchable to delineate different javac commands
        common.run_cmd(["echo", "\"-----------------------------------------------------------\""], args, "wpi")

        wpiDir = os.path.join(os.getcwd(), 'build/whole-program-inference')
        # if there is already a WPI directory, delete it and start over
        if os.path.isdir(wpiDir):
            shutil.rmtree(wpiDir)

        iteration = 0
        diffResult = 1
        stubDirs = []

        javac_switches = jc['javac_switches']
        cp = javac_switches['classpath']
        if javac_switches.has_key('processor') and len(processorArg) == 2:
            processorArg[1] += "," + javac_switches['processor']

        java_files = jc['java_files']

        # delombok
        delombok = False
        jars = cp.split(":")
        lombokjar = ""
        for jar in jars:
            # This should catch only the Lombok jar, because it's based
            # on Lombok's Maven coordinates. First is the Maven repo file structure;
            # second is the gradle cache's file structure.
            lombok_dirs = ["/org/projectlombok/lombok/", "/org.projectlombok/lombok/"]
            if any([x in jar for x in lombok_dirs]):
                lombokjar = jar
                break

        # must wait until here to supply the classpath without lombok
        if lombokjar != "":
            # delombok takes a directory as input rather than individual source files,
            # so this guesses at what the correct top-level directory is. It's a hack,
            # but it should work for Maven and Gradle projects that follow the default
            # conventions. For compilation to make sense, there must be at least one
            # Java file, so this access should be safe.
            anySrcFile = java_files[0]
            standardSrcDir = "src/main/java/"

            standardSrcIndex = anySrcFile.index(standardSrcDir)

            if standardSrcDir != -1:
                srcDir = anySrcFile[:standardSrcIndex]
                lombok_cmd = ["java", "-jar", lombokjar, "delombok",
                              srcDir + "/src/main/java/", "-d", srcDir + "/delombok/main/java",
                              "-c", cp]
                common.run_cmd(lombok_cmd, args, "wpi")
                # replace the original source files with the delombok'd code, so that
                # the actual javac commands don't need to be modified
                dir_util.copy_tree(srcDir + "/delombok/", srcDir + "/src/")

                # for modifying the checker command in each iteration
                delombok = True



        # include processor path in the class path if it is present
        pp = ''
        if javac_switches.has_key('processorpath'):
            pp = javac_switches['processorpath'] + ':'
        if args.quals:
            cp += args.quals + ':'
        if args.lib_dir:
            cp += pp + args.lib_dir + ':'

        other_args = []
        for k, v in javac_switches.items():
            if k not in banned_options and not k.startswith(banned_options_prefixes):
                if k == "source" or k == "target":
                    # if the source/target is < 8, change it to 8
                    if v in ["1.5", "5", "1.6", "6", "1.7", "7"]:
                        v = "8"
                    if v == "1.8":
                        v = "8"
                    # Do not use source/target, because Java 11 JVMs will
                    # crash on some classes, e.g.
                    # https://bugs.openjdk.java.net/browse/JDK-8212636.
                    # Use --release instead.
                    k = "-release"
                if v is None or v is not False:
                    other_args.append("-" + k)
                if v is not None and v is not True:
                    other_args.append(str(v))

        while diffResult != 0:

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

            # suppress all type.anno.before.modifier warnings, because delombok
            # prints annotations in the wrong place
            if delombok:
                iterationCheckerCmd.append("-AsuppressWarnings=type.anno.before.modifier")

            pprint.pformat(jc)

            cmd = iterationCheckerCmd + ["-classpath", cp] + processorArg + other_args + java_files
            stats = common.run_cmd(cmd, args, 'wpi')

            if stats['return_code'] == 0:
                return

            # process outputs
            # move the old wpi files, add them to stub path
            previousIterationDir = tempfile.mkdtemp(suffix="iteration" + str(iteration))
            try:
                stubs = os.listdir(wpiDir)
            except OSError as e:
                raise Exception("No WPI outputs were discovered. It is likely that WPI failed; "
                                "please check " + os.path.join(os.getcwd(), 'dljc-out')
                                + " . Original exception: " + str(e))

            for stub in stubs:
                shutil.move(os.path.join(wpiDir, stub), previousIterationDir)

            stubDirs.append(previousIterationDir)

            if len(stubDirs) > 1:
                dcmp = dircmp(stubDirs[-1], stubDirs[-2])
                diffResult = len(dcmp.diff_files)
