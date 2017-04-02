import jprint
import randoop
import randoop_old
import bixie
import graphtools
import chicory
import dyntrace
import dyntracecounts

# import soot
import check
import infer

TOOLS = {
  # 'soot'      : soot,
  'checker'   : check,
  'inference' : infer,
  'print'     : jprint,
  'randoop'   : randoop,
  'randoop_old': randoop_old,
  'bixie'     : bixie,
  'graphtool' : graphtools,
  'chicory'   : chicory,
  'dyntrace'  : dyntrace,
  'dyntracecounts' : dyntracecounts,
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
  if args.tool:
    for tool in parse_tools(args.tool):
      TOOLS[tool].run(args, javac_commands, jars)
