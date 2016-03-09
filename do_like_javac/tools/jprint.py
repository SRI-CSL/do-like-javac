import pprint

argparser = None

def run(args, javac_commands, jars):
  pp = pprint.PrettyPrinter(indent=2)
  for jc in javac_commands:
    pp.pprint(jc)
    javac_switches = jc['javac_switches']
  print("Target JARs (experimental):")
  pp.pprint(jars)
