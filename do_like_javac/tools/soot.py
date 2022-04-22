import argparse
import pprint

from . import common

argparser = argparse.ArgumentParser(add_help=False)
soot_group = argparser.add_argument_group('soot arguments')

soot_group.add_argument('-j', '--soot-jar', metavar='<soot-jar>',
                         action='store', default=None, dest='soot_jar',
                         help='Set the path to the soot jar.')

def run(args, javac_commands, jars):
    soot_command = ["java", "-jar", args.soot_jar]

    # now add the generic soot args that we want to use.
    # TODO: these should actually be parsed from command line.
    soot_command.extend(["-pp", "-src-prec", "c"])

    for jc in javac_commands:
        pprint.pformat(jc)
        javac_switches = jc['javac_switches']
        cp = javac_switches['classpath']
        class_dir = javac_switches['d']

        cmd = soot_command + ["-cp", cp, "-process-dir", class_dir]
        common.run_cmd(cmd, args, 'soot')


