import copy
import os

from . import common

argparser = None

def run(args, javac_commands, jars):
  bixie_jar = os.path.join(args.lib_dir, "bixie.jar")

  base_command = ["java",
                  "-jar", bixie_jar,
                  "-html", os.path.join(args.output_directory, 'bixie_report')]

  i = 1

  for jc in javac_commands:
    cmd = copy.copy(base_command)

    if common.classpath(jc):
      cmd.extend(["-cp", common.classpath(jc)])

    if common.class_directory(jc):
      cmd.extend(["-j", common.class_directory(jc)])

    if common.source_path(jc):
      cmd.extend(['-src', common.source_path(jc)])

    out_filename = 'bixie-report-{}.log'.format(i)
    cmd.extend(['-o', os.path.join(args.output_directory, out_filename)])

    common.run_cmd(cmd, args, 'bixie')
    i = i + 1
