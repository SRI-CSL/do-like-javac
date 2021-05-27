from . import common
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

    checker_command += getArgumentsByVersion(args.jdkVersion)

    for jc in javac_commands:
        ## What is the point of this pprint command, whose result is not used?
        pprint.pformat(jc)
        javac_switches = jc['javac_switches']
        cp = javac_switches['classpath']
        if args.quals:
            cp += args.quals + ':'
        paths = ['-classpath', cp]
        pp = ''
        if 'processorpath' in javac_switches:
            pp = javac_switches['processorpath'] + ':'
        if args.lib_dir:
            cp += pp + args.lib_dir + ':'
        java_files = jc['java_files']
        cmd = checker_command + ["-classpath", cp] + java_files
        common.run_cmd(cmd, args, 'check')

## other_args is other command-line arguments to javac
def getArgumentsByVersion(jdkVersion, other_args=[]):
    if jdkVersion is not None:
        version = int(jdkVersion)
    else:
        version = 8
    # add arguments depending on requested JDK version (default 8)
    result = []
    if version == 8:
        result += ['-J-Xbootclasspath/p:' + os.environ['CHECKERFRAMEWORK'] + '/checker/dist/javac.jar']
    elif version == 11:
        release_8 = False
        for i, str in enumerate(other_args):
            if str == '--release' and other_args[i+1] == "8":
                release_8 = True
        if not release_8:
            # Avoid javac "error: option --add-opens not allowed with target 1.8"
            result += ['-J--add-opens=jdk.compiler/com.sun.tools.javac.comp=ALL-UNNAMED']
    else:
        raise ValueError("the Checker Framework only supports Java versions 8 and 11")

    return result
