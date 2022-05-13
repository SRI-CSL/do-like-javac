import os

from . import dyntrace, common

argparser = None

def run(args, javac_commands, jars):
  javac_commands = common.get_module_javac_commands(args, javac_commands)
  i = 1
  out_dir = os.path.basename(args.output_directory)

  for jc in javac_commands:
    dyntrace.dyntrace(args, i, jc, out_dir, args.lib_dir, ['chicory'])
    i = i + 1
