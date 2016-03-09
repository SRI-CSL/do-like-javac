import os
import sys
import platform
import pprint
import subprocess
import traceback
import argparse

argparser = argparse.ArgumentParser(add_help=False)
graph_group = argparser.add_argument_group('graphtool arguments')

graph_group.add_argument('-j', '--jar', metavar='<jar>',
                         action='store',default=None,
                         help='Set the path to either prog2dfg.jar or apilearner.jar.')

def run(args, javac_commands, jars):
  jarfile = args.jar
  outdir = args.output_directory
  # first add the call to the soot jar.
  tool_command = []
  tool_command.extend(["java", "-jar", jarfile])

  pp = pprint.PrettyPrinter(indent=2)
  for jc in javac_commands:
    pp.pformat(jc)
    #jc['java_files']
    javac_switches = jc['javac_switches']
    class_dir = os.path.abspath(javac_switches['d'])

    java_files = jc['java_files']
    java_files_file = os.path.join(os.getcwd(), '__java_file_names.txt')
    with open(java_files_file, 'w') as f:
      for s in java_files:
        f.write(s)
        f.write("\n")

    current_outdir = os.path.join(outdir, class_dir.replace(os.getcwd(),'').replace(os.sep,"_"))

    cmd = tool_command + ["-o", current_outdir, "-j", class_dir, "-source", java_files_file ]
    print ("Running %s" % ' '.join(cmd))
    try:
      print (subprocess.check_output(cmd, stderr=subprocess.STDOUT))
    except:
      print ('calling {cmd} failed\n{trace}'.format(cmd=' '.join(cmd),trace=traceback.format_exc()))
