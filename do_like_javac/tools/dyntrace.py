import os
import argparse
import common
import tempfile

argparser = argparse.ArgumentParser(add_help=False)
dyntrace_group = argparser.add_argument_group('dyntrace arguments')

dyntrace_group.add_argument("--dyntrace-libs", metavar='<dyntrace-lib-dir>',
                            action='store', default=None, dest='dyn_lib_dir',
                            help='Library directory with JARs for randoop, daikon, and junit.')

def run(args, javac_commands, jars):
  i = 1

  for jc in javac_commands:
    dyntrace(i, jc, args.dyn_lib_dir)
    i = i + 1

def dyntrace(i, java_command, lib_dir):
  classpath = common.classpath(java_command)
  classdir = os.path.abspath(common.class_directory(java_command))

  randoop_driver = "RegressionTestDriver"
  test_src_dir = "test-src{}".format(i)
  test_class_directory = "test-classes{}".format(i)
  dtrace_file_name="{}-{}.dtrace.gz".format(randoop_driver, i)

  base_classpath = classpath + ":" + classdir
  randoop_classpath = base_classpath + ":" + os.path.join(lib_dir, "randoop-2.1.4.jar")
  compile_classpath = base_classpath + ":" + os.path.join(lib_dir, "junit-4.12.jar")
  chicory_classpath = compile_classpath + ":" + os.path.abspath(test_class_directory) + ":" + os.path.join(lib_dir, "daikon.jar")

  classes = get_classes(classdir)

  class_list_file = make_class_list(classes)
  time_limit = 10
  output_limit = 20

  generate_tests(randoop_classpath, class_list_file, test_src_dir, time_limit, output_limit)

  files_to_compile = get_files_to_compile(test_src_dir)

  compile_test_cases(compile_classpath, test_class_directory, files_to_compile)
  run_chicory(chicory_classpath, classes, randoop_driver, dtrace_file_name)

def get_classes(classdir):
  classes = []
  for root, dirs, files in os.walk(classdir):
    for file in files:
      if file.endswith('.class'):
        classfile = os.path.join(root, file)
        classname = classfile.replace(classdir + "/", '').replace('.class','').replace('/','.')
        classes.append(classname)
  return classes

def make_class_list(classes):
  fd, filename = tempfile.mkstemp(suffix='.txt', prefix='clist', text=True)

  f = os.fdopen(fd, 'w')
  for c in classes:
    f.write(c)
    f.write('\n')

  f.close()

  return filename

def generate_tests(randoop_classpath, class_list_file, test_src_dir, time_limit, output_limit):
  randoop_command = ["java", "-ea",
                     "-classpath", randoop_classpath,
                     "randoop.main.Main", "gentests",
                     '--classlist={}'.format(class_list_file),
                     "--timelimit={}".format(time_limit),
                     "--junit-reflection-allowed=false",
                     "--silently-ignore-bad-class-names=true",
                     '--junit-output-dir={}'.format(test_src_dir)]

  if output_limit and output_limit > 0:
    randoop_command.append('--outputlimit={}'.format(output_limit))

  common.run_cmd(randoop_command)

def get_files_to_compile(test_src_dir):
  jfiles = []
  for root, dirs, files in os.walk(test_src_dir):
    for file in files:
      if file.endswith('.java'):
        jfiles.append(os.path.join(root, file))

  return jfiles

def compile_test_cases(compile_classpath, test_class_directory, files_to_compile):
  if not os.path.exists(test_class_directory):
    os.mkdir(test_class_directory)

  compile_command = ["javac", "-g",
                     "-classpath", compile_classpath,
                     "-d", test_class_directory]
  compile_command.extend(files_to_compile)

  common.run_cmd(compile_command)

def get_namespace(class_name):
  if "." not in class_name:
    return class_name
  else:
    return class_name[0:class_name.rfind(".")]


def run_chicory(chicory_classpath, classes_to_include, main_class, dtrace_file_name):
  # TODO Do we want ErrorTestDriver or main_class here?
  inclusion_regex = "--ppt-select-pattern=^(ErrorTestDriver|ErrorTest(\\d)+"
  for class_name in classes_to_include:
    inclusion_regex = inclusion_regex + "|" + get_namespace(class_name)
  inclusion_regex = inclusion_regex + ")\\S*"

  chicory_command = ["java",
                     "-classpath", chicory_classpath,
                     "daikon.Chicory", inclusion_regex,
                     "--daikon",
                     "--dtrace-file={}".format(dtrace_file_name),
                     main_class]

  common.run_cmd(chicory_command)
