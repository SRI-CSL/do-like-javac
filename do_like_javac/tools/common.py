import sys
import subprocess
import traceback
import os

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

def run_cmd(cmd):
  print ("Running %s" % ' '.join(cmd))
  try:
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for line in iter(process.stdout.readline, b''):
      sys.stdout.write(line)
      sys.stdout.flush()
    process.stdout.close()
    process.wait()
  except:
    print ('calling {cmd} failed\n{trace}'.format(cmd=' '.join(cmd),trace=traceback.format_exc()))
