import argparse
import json
import os

from . import common, jsoninv

argparser = argparse.ArgumentParser(add_help=False)
dyntrace_group = argparser.add_argument_group('dyntrace arguments')

dyntrace_group.add_argument('-X', '--daikon-xml',
                        action='store_true',
                        help='Have Daikon emit XML')

# choose error revealing driver
dyntrace_group.add_argument('--error-driver',
                        action='store_true',
                        dest='error_driver',
                        help='Chose Error Revealing Driver')

no_jdk = False
no_ternary = False

def run(args, javac_commands, jars):
  i = 1
  out_dir = os.path.basename(args.output_directory)

  for jc in javac_commands:
    dyntrace(args, i, jc, out_dir, args.lib_dir)
    i = i + 1

def dyntrace(args, i, java_command, out_dir, lib_dir, run_parts=['randoop','chicory']):
  def lib(jar):
    return os.path.join(lib_dir, jar)

  classpath = common.classpath(java_command)
  classdir = os.path.abspath(common.class_directory(java_command))

  randoop_driver = "RegressionTestDriver"
  if args.error_driver:
    randoop_driver = "ErrorTestDriver"
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
  # randoop needs to be on compile classpath due to replacement of System.exit with SystemExitCalledError
  compile_classpath = lib("junit-4.12.jar") + ":" + randoop_classpath
  chicory_classpath = ':'.join([os.path.abspath(test_class_directory),
                                os.path.join(os.environ.get('DAIKONDIR'), 'daikon.jar'),
                                os.path.join(os.environ.get('DAIKONDIR'), 'java'),
                                lib("hamcrest-core-1.3.jar"),
                                compile_classpath])
  replace_call_classpath = lib('replacecall.jar')

  if 'randoop' in run_parts:
    classes = sorted(common.get_classes(java_command))
    class_list_file = make_class_list(test_class_directory, classes)
    junit_after_path = get_special_file("junit-after", out_dir, i)

    generate_tests(args, randoop_classpath, class_list_file, test_src_dir, junit_after_path, replace_call_classpath)
    files_to_compile = get_files_to_compile(test_src_dir)
    if not files_to_compile:
      return
    compile_test_cases(args, compile_classpath, test_class_directory, files_to_compile)

  if 'chicory' in run_parts:
    selects = get_select_list(classdir)
    omit_file_path = get_special_file("omit-list", out_dir, i)
    omits = get_omit_list(omit_file_path)

    run_dyncomp(args, chicory_classpath, randoop_driver, test_class_directory, selects, omits)
    run_chicory(args, chicory_classpath, randoop_driver, test_class_directory, selects, omits)
    run_daikon(args, chicory_classpath, test_class_directory, False)
    if 'invcounts' in run_parts:
      run_daikon(args, chicory_classpath, test_class_directory, True)

    if args.daikon_xml:
      daikon_print_xml(args, chicory_classpath, test_class_directory)

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

def get_special_file(special_type, out_dir, i):
  candidate = os.path.join(out_dir, f"{special_type}.{i}")
  if os.path.isfile(candidate):
    return os.path.normpath(candidate)

  candidate = os.path.join(out_dir, special_type)
  if os.path.isfile(candidate):
    return os.path.normpath(candidate)

  return None

def get_omit_list(omit_file_path):
  global no_jdk, no_ternary
  no_jdk = False
  no_ternary = False
  omits = []

  if omit_file_path:
    with open(omit_file_path, 'r') as f:
      for line in f:
        if line.strip() == "NO-JDK":
            no_jdk = True
        elif line.strip() == "NO-TERNARY":
            no_ternary = True
        else:
            omit = "--ppt-omit-pattern=" + line.strip()
            omits.append(omit)
  return omits

def make_class_list(out_dir, classes):
  with open(os.path.join(out_dir,"classlist.txt"), 'w') as class_file:
    for c in classes:
      if "package-info" not in c:
        class_file.write(c)
        class_file.write('\n')
    class_file.flush()
    return class_file.name

def generate_tests(args, classpath, class_list_file, test_src_dir, junit_after_path, rc_classpath, time_limit=200, output_limit=4000):

  # Methods to be omitted due to non-determinism.
  omitted_methods = "\"(org\\.la4j\\.operation\\.ooplace\\.OoPlaceKroneckerProduct\\.applyCommon)|(PseudoOracle\\.verifyFace)|(org\\.znerd\\.math\\.NumberCentral\\.createRandomInteger)|(org\\.jbox2d\\.common\\.MathUtils\\.randomFloat.*)|(org\\.jbox2d\\.utests\\.MathTest\\.testFastMath)|(org\\.jbox2d\\.testbed\\.tests\\.DynamicTreeTest.*)|(org\\.la4j\\.Matrix.*)\""

  selection_log_file = "dljc-out/selection-log.txt"
  operation_log_file = "dljc-out/operation-history-log.txt"
  randoop_log_file = "dljc-out/randoop-log.txt"

  randoop_command = ["java", "-ea",
                     "-classpath", classpath,
                     f"-Xbootclasspath/a:{rc_classpath}",
                     f"-javaagent:{rc_classpath}",
                     "randoop.main.Main", "gentests",
                     f"--classlist={class_list_file}",
                     f"--time-limit={time_limit}",
                     f"--omit-methods={omitted_methods}",
                     "--junit-reflection-allowed=false",
                     "--flaky-test-behavior=DISCARD",
                     "--usethreads=true",
                     "--call-timeout=5",
                     "--silently-ignore-bad-class-names=true",
                     f"--junit-output-dir={test_src_dir}",
                     # Uncomment these lines to produce Randoop debugging logs
                     f"--log={randoop_log_file}",
                     f"--selection-log={selection_log_file}",
                     f"--operation-history-log={operation_log_file}"]

  if junit_after_path:
    randoop_command.append(f"--junit-after-all={junit_after_path}")

  if output_limit and output_limit > 0:
    randoop_command.append(f'--output-limit={output_limit}')

  print("Running command", " ".join(randoop_command))

  common.run_cmd(randoop_command, args, 'randoop')

def get_files_to_compile(test_src_dir):
  jfiles = []
  for root, dirs, files in os.walk(test_src_dir):
    for file in files:
      if file.endswith('.java'):
        jfiles.append(os.path.join(root, file))

  return jfiles

def compile_test_cases(args, classpath, test_class_directory, files_to_compile):
  compile_command = ["javac", "-g",
                     "-classpath", classpath,
                     "-d", test_class_directory]
  compile_command.extend(files_to_compile)

  common.run_cmd(compile_command, args, 'randoop')

def run_chicory(args, classpath, main_class, out_dir, selects=[], omits=[]):
  chicory_command = ["java", "-Xmx3G",
                     "-classpath", classpath,
                     "daikon.Chicory",
                     f"--output_dir={out_dir}"]

  randoop_driver = "RegressionTestDriver"
  if args.error_driver:
    randoop_driver = "ErrorTestDriver"

  decls_dyn_comp_file = f"{randoop_driver}.decls-DynComp"

  dc_out_path = os.path.join(out_dir, decls_dyn_comp_file)
  chicory_command.append("--comparability-file={}".format(dc_out_path))

  chicory_command.extend(selects)
  chicory_command.extend(omits)
  chicory_command.append(main_class)

  print("Running command", " ".join(chicory_command))

  common.run_cmd(chicory_command, args, 'chicory')


def run_dyncomp(args, classpath, main_class, out_dir, selects=[], omits=[]):
  dyncomp_command = ["java", "-Xmx3G",
                     "-classpath", classpath,
                     "daikon.DynComp",
                     "--approximate-omitted-ppts",
                     f"--output-dir={out_dir}"]

  if no_jdk:
    dyncomp_command.append("--rt-file=none")
  dyncomp_command.extend(selects)
  dyncomp_command.extend(omits)
  dyncomp_command.append(main_class)

  print("Running command", " ".join(dyncomp_command))

  common.run_cmd(dyncomp_command, args, 'dyncomp')

def run_daikon(args, classpath, out_dir, invcounts):
  daikon_command = ["java", "-Xmx4G",
                     "-classpath", classpath,
                     "daikon.Daikon",
                     "-o", os.path.join(out_dir, "invariants.gz")]
  if invcounts:
    daikon_command.append("--config_option")
    daikon_command.append("daikon.Daikon.calc_possible_invs=true")
  if no_ternary:
    daikon_command.append("--config_option")
    daikon_command.append("daikon.inv.ternary.threeScalar.LinearTernary.enabled=false")
    daikon_command.append("--config_option")
    daikon_command.append("daikon.inv.ternary.threeScalar.LinearTernaryFloat.enabled=false")
  daikon_command.append(os.path.join(out_dir, "RegressionTestDriver.dtrace.gz"))

  print("Running command", " ".join(daikon_command))

  common.run_cmd(daikon_command, args, 'daikon')

def daikon_print_xml(args, classpath, out_dir):
  daikon_command = ["java", "-Xmx4G",
                    "-classpath", classpath,
                    "daikon.PrintInvariants",
                    "--wrap_xml",
                    "--output", os.path.join(out_dir, "invariants.xml"),
                    os.path.join(out_dir, "invariants.gz")]

  common.run_cmd(daikon_command, args, 'daikon')
  js = jsoninv.generate_json_invariants(args, out_dir)
  with open(os.path.join(out_dir, 'invariants.json'), 'w') as f:
    json.dump(js, f)
