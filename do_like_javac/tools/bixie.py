import os
import common

argparser = None

def run(args, javac_commands, jars):
  bixie_jar = os.path.join(args.lib_dir, "bixie.jar")



  bixie_command = ["java", "-jar", bixie_jar,
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
