import argparse
import copy
import os

from . import common

argparser = argparse.ArgumentParser(add_help=False)
graph_group = argparser.add_argument_group('graphtool arguments')

graph_group.add_argument('--graph-jar', metavar='<graphtool-jar>',
                         action='store', default=None, dest='graph_jar',
                         help='Path to prog2dfg.jar, apilearner.jar or augmaker.jar')

# augmaker only arguments
graph_group.add_argument('--batch-size', metavar='<batches>',
                         action='store', default=-1, dest='batches',
                         help='batch size (augmaker only)')
graph_group.add_argument('--project-file', metavar='<projectfile-file>',
                         action='store', default=None, dest='projectfile',
                         help='list of projects to process (augmaker only)')

def run(args, javac_commands, jars):
  if not args.graph_jar:
    print("Could not run graph tool: missing arg --graph-jar")
    return

  skip_building = "augmaker.jar" in str(args.graph_jar)
  
  dot_dir = os.path.join(args.output_directory, "dot")
  if not os.path.isdir(dot_dir):
    os.makedirs(dot_dir)

  tool_command = ["java", "-jar", args.graph_jar]
  if skip_building:
    # augmaker.jar does not require projects to be built.
    # Additionally, augmaker.jar does not have
    # a Main-Class defined in the manifest file. Consequently,
    # it must be executed differently, using its cli rather
    # than using its jar file. To do this, we must override
    # the tool_command variable.
    tool_command = ["java", "-cp", f".:{args.graph_jar}:*", 'com.sri.augmake.AugmakerCli']
    cmd = copy.copy(tool_command)
    cmd.extend(["--outputdir", dot_dir])
    cmd.extend(["--howmany", args.batches])
    cmd.extend(["--projectfile", args.projectfile])
    cmd.extend(["--dotpretty", "dot"])
    common.run_cmd(cmd, args, 'graphtools')
  else:
    # prog2dfg.jar and apilearner.jar require projects to be built first
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
      
      print(f"Running command", " ".join(cmd))

      common.run_cmd(cmd, args, 'graphtools')
