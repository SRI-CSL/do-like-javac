import json

argparser = None

def run(args, javac_commands, jars):
  print(json.dumps(
    {
      "javac_commands": javac_commands,
      "jars": jars
    },
    indent = 2,
    separators = (',', ': ')
  ));
