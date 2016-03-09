import check
import graphtools
import infer
import jprint
import randoop
import soot

TOOLS = {
  'soot' : soot,
  'checker' : check,
  'inference' : infer,
  'print' : jprint,
  'randoop' : randoop,
  'graphtool' : graphtools,
}

def parsers():
  return [mod.argparser for name, mod in TOOLS.iteritems() if mod.argparser]

def run(args, javac_commands, jars):
  if args.tool:
      TOOLS[args.tool].run(args, javac_commands, jars)
