import os
import common
import tempfile

argparser = None

def run(args, javac_commands, jars):
  i = 1
  out_dir = os.path.basename(args.output_directory)

  for jc in javac_commands:
    dyntrace(i, jc, out_dir, args.lib_dir)
    i = i + 1

def dyntrace(i, java_command, out_dir, lib_dir, run_parts=['randoop','chicory']):
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

  randoop_classpath = os.path.join(lib_dir, "randoop.jar") + ":" + base_classpath
  compile_classpath = os.path.join(lib_dir, "junit-4.12.jar") + ":" + base_classpath
  chicory_classpath = os.path.abspath(test_class_directory) + ":" + os.path.join(lib_dir, "daikon.jar") + ":" + os.path.join(lib_dir, "hamcrest-core-1.3.jar") + ":" + compile_classpath

  classes = get_classes(classdir)

  if 'randoop' in run_parts:
    class_list_file = make_class_list(classes)
    time_limit = 300
    output_limit = 30

    generate_tests(randoop_classpath, class_list_file, test_src_dir, time_limit, output_limit)

    files_to_compile = get_files_to_compile(test_src_dir)

    compile_test_cases(compile_classpath, test_class_directory, files_to_compile)

  if 'chicory' in run_parts:
    run_dyncomp(chicory_classpath, classdir, randoop_driver, test_class_directory)
    run_chicory(chicory_classpath, classdir, randoop_driver, test_class_directory)
    run_daikon(chicory_classpath, test_class_directory)

def get_classes(classdir):
  classes = []
  for root, dirs, files in os.walk(classdir):
    for file in files:
      if file.endswith('.class'):
        classfile = os.path.join(root, file)
        classname = classfile.replace(classdir + "/", '').replace('.class','').replace('/','.')
        classes.append(classname)
  return sorted(classes)

def get_select_list(classdir):
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

def get_omit_list(classdir):
  omits = []
  if os.path.isfile('omit-list'):
    with open('omit-list', 'r') as f:
      for line in f:
        omit = "--ppt-omit-pattern=" + line.strip()
        omits.append(omit)
  return omits

def make_class_list(classes):
  with tempfile.NamedTemporaryFile('w', suffix='.txt', prefix='clist', delete=False) as class_file:
    for c in classes:
      class_file.write(c)
      class_file.write('\n')
    class_file.flush()
    return class_file.name

def generate_tests(randoop_classpath, class_list_file, test_src_dir, time_limit, output_limit):
  randoop_command = ["java", "-ea",
                     "-classpath", randoop_classpath,
                     "randoop.main.Main", "gentests",
                     '--classlist={}'.format(class_list_file),
                     "--timelimit={}".format(time_limit),
                     "--junit-reflection-allowed=false",
                     "--ignore-flaky-tests=true",
                     "--junit-after-all=junit-after-code",
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
  compile_command = ["javac", "-g",
                     "-classpath", compile_classpath,
                     "-d", test_class_directory]
  compile_command.extend(files_to_compile)

  common.run_cmd(compile_command)


def run_chicory(chicory_classpath, classdir, main_class, out_dir):
  selects = get_select_list(classdir)
  omits = get_omit_list(classdir)
  chicory_command = ["java",
                     "-classpath", chicory_classpath,
                     "daikon.Chicory",
                     "--comparability-file={}/RegressionTestDriver.decls-DynComp".format(out_dir),
                     "--output_dir={}".format(out_dir)]
  for select in selects:
    chicory_command.append(select)
  for omit in omits:
    chicory_command.append(omit)
  chicory_command.append(main_class)

  common.run_cmd(chicory_command)


def run_dyncomp(dyncomp_classpath, classdir, main_class, out_dir):
  selects = get_select_list(classdir)
  omits = get_omit_list(classdir)
  dyncomp_command = ["java",
                     "-classpath", dyncomp_classpath,
                     "daikon.DynComp",
                     "--no-cset-file",
                     "--output-dir={}".format(out_dir)]
  for select in selects:
    dyncomp_command.append(select)
  for omit in omits:
    dyncomp_command.append(omit)
  dyncomp_command.append(main_class)

  common.run_cmd(dyncomp_command)


def run_daikon(daikon_classpath, out_dir):
  daikon_command = ["java",
                     "-classpath", daikon_classpath,
                     "daikon.Daikon",
                     "-o", out_dir+"/invariants.gz",
                     out_dir+"/RegressionTestDriver.dtrace.gz"]

  common.run_cmd(daikon_command)

