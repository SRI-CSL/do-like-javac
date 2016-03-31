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

def check_tool(tool):
  if tool in TOOLS:
    return tool
  else:
    print "ERROR: Could not find tool {}".format(tool)
    return None

def parse_tools(tools):
  return [tool for tool in tools.split(',') if check_tool(tool)]

def run(args, javac_commands, jars):
  for tool in parse_tools(args.tool):
    TOOLS[tool].run(args, javac_commands, jars)
