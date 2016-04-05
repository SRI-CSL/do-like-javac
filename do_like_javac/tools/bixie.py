import os
import argparse
import common

argparser = argparse.ArgumentParser(add_help=False)
bixie_group = argparser.add_argument_group('bixie arguments')

bixie_group.add_argument('--bixie-jar', metavar='<bixie-jar>',
                         action='store',default=None, dest='bixie_jar',
                         help='Path to bixie.jar')

def run(args, javac_commands, jars):
  if not args.bixie_jar:
    print "Could not run bixie tool: missing arg --bixie-jar"
    return

  bixie_command = ["java", "-jar", args.bixie_jar,
                    "-html", os.path.join(args.output_directory, 'bixie_report')]

  i = 1

  for jc in javac_commands:
    javac_switches = jc['javac_switches']

    cmd = bixie_command + ["-cp", common.classpath(jc),
                            "-j", common.class_directory(jc)]
    if common.source_path(jc):
      cmd.extend(['-src', common.source_path(jc)])

    out_filename = 'bixie-report-{}.log'.format(i)
    cmd.extend(['-o', os.path.join(args.output_directory, out_filename)])

    common.run_cmd(cmd)
    i = i + 1
