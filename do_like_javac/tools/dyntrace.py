import os
import common
import tempfile

argparser = None
no_jdk = False

def run(args, javac_commands, jars):
  i = 1
  out_dir = os.path.basename(args.output_directory)

  for jc in javac_commands:
    dyntrace(i, jc, out_dir, args.lib_dir)
    i = i + 1

def full_daikon_available():
  return os.environ.get('DAIKONDIR')

def dyntrace(i, java_command, out_dir, lib_dir, run_parts=['randoop','chicory']):
  def lib(jar):
    return os.path.join(lib_dir, jar)

  classpath = common.classpath(java_command)
  classdir = os.path.abspath(common.class_directory(java_command))

  randoop_driver = "RegressionTestDriver"
  test_src_dir = os.path.join(out_dir, "test-src{}".format(i))
  test_class_directory = os.path.join(out_dir, "test-classes{}".format(i))

  if not os.path.exists(test_class_directory):
    os.mkdir(test_class_directory)

  if classpath:
    base_classpath = classpath + ":" + classdir
  else:
    base_classpath = classdir

  with open(os.path.join(test_class_directory, 'classpath.txt'), 'w') as f:
    f.write(base_classpath)
  with open(os.path.join(test_class_directory, 'classdir.txt'), 'w') as f:
    f.write(classdir)

  randoop_classpath = lib('randoop.jar') + ":" + base_classpath
  compile_classpath = lib("junit-4.12.jar") + ":" + base_classpath
  chicory_classpath = os.path.abspath(test_class_directory) + ":" + \
                      lib("daikon.jar") + ":" +\
                      lib("hamcrest-core-1.3.jar") + ":" + \
                      compile_classpath

  if 'randoop' in run_parts:
    classes = sorted(common.get_classes(java_command))
    class_list_file = make_class_list(test_class_directory, classes)

    generate_tests(randoop_classpath, class_list_file, test_src_dir)
    files_to_compile = get_files_to_compile(test_src_dir)
    compile_test_cases(compile_classpath, test_class_directory, files_to_compile)

  if 'chicory' in run_parts:
    selects = get_select_list(classdir)
    omits = get_omit_list(os.path.join(out_dir, "omit-list"), classdir)

    if full_daikon_available():
      run_dyncomp(chicory_classpath, randoop_driver, test_class_directory, selects, omits)
    run_chicory(chicory_classpath, randoop_driver, test_class_directory, selects, omits)
    run_daikon(chicory_classpath, test_class_directory)

def get_select_list(classdir):
  """Get a list of all directories under classdir containing class files."""
  selects = []
  last_add = " " # guaranteed not to match
  for root, dirs, files in os.walk(classdir):
    if not root.startswith(last_add):
      for file in files:
        if file.endswith('.class'):
          if root == classdir:
            break
          last_add = root
          select = "--ppt-select-pattern=" + root.replace(classdir + "/", '').replace('/','.')
          selects.append(select)
          break
  return selects

def get_omit_list(omit_file_path, classdir):
  global no_jdk
  omits = []

  if os.path.isfile(omit_file_path):
    with open(omit_file_path, 'r') as f:
      for line in f:
        if line.strip() == "NO-JDK":
            no_jdk = True
        else:
            omit = "--ppt-omit-pattern=" + line.strip()
            omits.append(omit)
  return omits

def make_class_list(out_dir, classes):
  with open(os.path.join(out_dir,"classlist.txt"), 'w') as class_file:
    for c in classes:
      class_file.write(c)
      class_file.write('\n')
    class_file.flush()
    return class_file.name

def generate_tests(classpath, class_list_file, test_src_dir, time_limit=60, output_limit=2000):
  randoop_command = ["java", "-ea",
                     "-classpath", classpath,
                     "randoop.main.Main", "gentests",
                     '--classlist={}'.format(class_list_file),
                     "--timelimit={}".format(time_limit),
                     "--junit-reflection-allowed=false",
                     "--ignore-flaky-tests=true",
                     "--silently-ignore-bad-class-names=true",
                     '--junit-output-dir={}'.format(test_src_dir)]

  junit_after_path = os.path.normpath(os.path.join(test_src_dir, "..", "junit-after"))
  if os.path.exists(junit_after_path):
    randoop_command.append("--junit-after-all={}".format(junit_after_path))

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

def compile_test_cases(classpath, test_class_directory, files_to_compile):
  compile_command = ["javac", "-g",
                     "-classpath", classpath,
                     "-d", test_class_directory]
  compile_command.extend(files_to_compile)

  common.run_cmd(compile_command)


def run_chicory(classpath, main_class, out_dir, selects=[], omits=[]):
  chicory_command = ["java",
                     "-classpath", classpath,
                     "daikon.Chicory",
                     "--output_dir={}".format(out_dir)]

  if full_daikon_available():
    dc_out_path = os.path.join(out_dir, "RegressionTestDriver.decls-DynComp")
    chicory_command.append("--comparability-file={}".format(dc_out_path))

  chicory_command.extend(selects)
  chicory_command.extend(omits)
  chicory_command.append(main_class)

  common.run_cmd(chicory_command)


def run_dyncomp(classpath, main_class, out_dir, selects=[], omits=[]):
  dyncomp_command = ["java",
                     "-classpath", classpath,
                     "daikon.DynComp",
                     "--approximate-omitted-ppts",
                     "--output-dir={}".format(out_dir)]

  if no_jdk:
      dyncomp_command.append("--rt-file=none")
  dyncomp_command.extend(selects)
  dyncomp_command.extend(omits)
  dyncomp_command.append(main_class)

  common.run_cmd(dyncomp_command)

def run_daikon(classpath, out_dir):
  daikon_command = ["java",
                     "-classpath", classpath,
                     "daikon.Daikon",
#                    "--config_option", "daikon.Daikon.calc_possible_invs=true",
                     "-o", os.path.join(out_dir, "invariants.gz"),
                     os.path.join(out_dir, "RegressionTestDriver.dtrace.gz")]

  common.run_cmd(daikon_command)
