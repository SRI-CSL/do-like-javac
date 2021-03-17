import os
import argparse
from . import common

argparser = argparse.ArgumentParser(add_help=False)
graph_group = argparser.add_argument_group('graphtool arguments')

graph_group.add_argument('--graph-jar', metavar='<graphtool-jar>',
                         action='store',default=None, dest='graph_jar',
                         help='Path to prog2dfg.jar or apilearner.jar')

def run(args, javac_commands, jars):
  if not args.graph_jar:
    print("Could not run graph tool: missing arg --graph-jar")
    return

  tool_command = ["java", "-jar", args.graph_jar]

  dot_dir = os.path.join(args.output_directory, "dot")
  if not os.path.isdir(dot_dir):
    os.makedirs(dot_dir)

  for jc in javac_commands:
    java_files = jc['java_files']
    java_files_file = os.path.join(os.getcwd(), '__java_file_names.txt')

    class_dir = common.class_directory(jc)

    with open(java_files_file, 'w') as f:
      for s in java_files:
        f.write(s)
        f.write("\n")

    current_outdir = os.path.join(dot_dir,
                                  class_dir.replace(os.getcwd(),'').replace(os.sep,"_"))

    cmd = tool_command + ["-o", current_outdir,
                          "-j", class_dir,
                          "-all",
                          "-source", java_files_file]

    common.run_cmd(cmd, args, 'graphtools')
