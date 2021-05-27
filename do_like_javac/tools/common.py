import sys, os, traceback
import subprocess
import timeit
from threading import Timer

def log(args, tool, message):
  with open(os.path.join(args.output_directory, '{}.log'.format(tool)), 'a') as f:
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
      classes.extend([os.path.join(root,file) for file in files if '.class' in file])

  return classes

def get_classes(javac_command):
  def class_file_to_class_name(classdir, class_file):
    return class_file.replace(classdir + "/", '').replace('.class','').replace('/','.')

  classdir = class_directory(javac_command)
  return [class_file_to_class_name(classdir, file) for file in get_class_files(javac_command)]

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
  timer = None
  out = None
  out_file = None
  # Without quoting, empty arguments don't appear in friendly_cmd
  friendly_cmd = ' '.join("'" + elt + "'" for elt in cmd)

  if args and args.verbose and args.log_to_stderr:
    out = sys.stderr
  elif tool:
    out_file = os.path.join(args.output_directory, tool + ".log")
    out = open(out_file, 'a')

  def output(line):
    if out:
      out.write(line)
      out.flush()

  def kill_proc(proc, stats):
    output("Timed out after {} seconds on {}\n".format(args.timeout, friendly_cmd))
    stats['timed_out'] = True
    proc.kill()

  # output("\nPath: " + os.environ['PATH'] + "\n")
  output("\nRunning {}\n\n".format(friendly_cmd))

  try:
    start_time = timeit.default_timer()
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    if args and args.timeout:
      timer = Timer(args.timeout, kill_proc, [process, stats])
      timer.start()

    for line in iter(process.stdout.readline, b''):
      stats['output'] = stats['output'] + line.decode()
      output(line.decode())

    process.stdout.close()
    stats['return_code'] = process.wait()
    stats['time'] = timeit.default_timer() - start_time
    if timer:
      timer.cancel()

  except:
    output('calling {cmd} failed\n{trace}\n'.format(cmd=friendly_cmd,trace=traceback.format_exc()))

  if out_file:
    out.close()

  return stats
