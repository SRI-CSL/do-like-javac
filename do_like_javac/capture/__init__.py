from . import ant, gradle, javac, mvn

capture_modules = [ant, gradle, javac, mvn]

def supported_commands():
  module_commands = [mod.supported_commands for mod in capture_modules]
  return [cmd for commands in module_commands for cmd in commands]

def get_capturer(cmd):
  for mod in capture_modules:
    if cmd in mod.supported_commands:
      return mod
  return None
