import os
import subprocess
import sys
import timeit
import traceback


def log(args, tool, message):
  with open(os.path.join(args.output_directory, f"{tool}-stdout.log"), 'a') as f:
    f.write(message)
    f.flush()

def classpath(javac_command):
  if 'javac_switches' in javac_command:
    switches = javac_command['javac_switches']
    if 'cp' in switches:
      return switches['cp']
    if 'classpath' in switches:
      return switches['classpath']
  return None

def class_directory(javac_command):
  if 'javac_switches' in javac_command:
    switches = javac_command['javac_switches']
    if 'd' in switches:
      return switches['d']
  return None

def get_class_files(javac_command):
  classes = []
  classdir = class_directory(javac_command)

  if classdir:
    for root, dirs, files in os.walk(classdir):
      classes.extend([os.path.join(root,file)
                      for file in files if '.class' in file])

  return classes

def get_classes(javac_command):
  def class_file_to_class_name(classdir, class_file):
    return class_file.replace(classdir + "/", '').replace('.class','').replace('/','.')

  classdir = class_directory(javac_command)
  return [class_file_to_class_name(classdir, file)
          for file in get_class_files(javac_command)]

def source_path(javac_command):
  if 'javac_switches' in javac_command:
    switches = javac_command['javac_switches']
    if 'sourcepath' in switches:
      return switches['sourcepath']
    elif 'java_files' in javac_command:
      return os.pathsep.join(javac_command['java_files'])
  return None

def run_cmd(cmd, args=None, tool=None):
  stats = {'timed_out': False,
           'output': ''}
  # timer = None
  out = None
  out_file = None
  # Without quoting, empty arguments don't appear in friendly_cmd
  friendly_cmd = ' '.join("'" + elt + "'" for elt in cmd)

  if args and args.verbose and args.log_to_stderr:
    out = sys.stderr
  elif tool:
    out_file = os.path.join(args.output_directory, f"{tool}-stdout.log")
    out = open(out_file, 'a')

  def output(line):
    if out:
      out.write(line)
      out.flush()

  output(f"Running {friendly_cmd}\n\n")

  try:
    start_time = timeit.default_timer()
    timeout = args and args.timeout

    process = subprocess.run(cmd, timeout=timeout,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT)

    stats['output'] = process.stdout.decode('utf-8')
    output(stats['output'])

    stats['time'] = timeit.default_timer() - start_time
    stats['return_code'] = process.returncode

  except subprocess.TimeoutExpired as e:
    output(f"Timed out after {args.timeout} seconds on {friendly_cmd}\n")
    stats['timed_out'] = True
  except Exception as e:
    print(e)
    output(f'calling {friendly_cmd} failed\n{traceback.format_exc()}\n')

  if out_file:
    out.close()

  return stats
