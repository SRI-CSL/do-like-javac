import os

from . import dyntrace

argparser = None

def run(args, javac_commands, jars):
  i = 1
  out_dir = os.path.basename(args.output_directory)

  for jc in javac_commands:
    dyntrace.dyntrace(args, i, jc, out_dir, args.lib_dir, ['chicory'])
    i = i + 1
