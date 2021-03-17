import os
import pprint
import shutil
import glob
import urllib.request, urllib.parse, urllib.error

argparser = None

def run(args, javac_commands, jars):
    pp = pprint.PrettyPrinter(indent=2)
    i = 0
    for jc in javac_commands:
        javac_switches = jc['javac_switches']
        cp = javac_switches['classpath']
        class_file_dir = javac_switches['d']
        class_files = [y for x in os.walk(class_file_dir) for y in glob.glob(os.path.join(x[0], '*.class'))]

        if len(class_files)==0:
            continue

        out_dir_name = "__randoop_%04d" % (i)
        if not os.path.exists(out_dir_name):
            os.makedirs(out_dir_name)

        class_files_file_name = os.path.join(out_dir_name, 'class_files.txt')
        print("Creating list of files %d in %s." % (len(class_files), os.path.abspath(out_dir_name)))
        with open(class_files_file_name, mode='w') as myfile:
            for class_file_name in class_files:
                myfile.write(get_qualified_class_name_from_file(class_file_name, class_file_dir))
                myfile.write(os.linesep)

        (randoop_jar, junit_jar, hamcrest_jar) = find_or_download_jars()

        cp_entries = cp.split(os.pathsep)
        clean_cp = list()
        clean_cp.append(randoop_jar)
        clean_cp.append(class_file_dir)

        lib_dir_name = "__randoop_libs"
        if not os.path.exists(lib_dir_name):
            os.makedirs(lib_dir_name)

        for cp_entry in cp_entries:
            if cp_entry.endswith(".jar"):
                #check if the jar is in a sub directory of the project.
                #if not copy it into a new subdirectory and add the
                #corresponding classpath entry.
                if not os.path.realpath(cp_entry).startswith(os.getcwd()):
                    new_jar_name = os.path.join(lib_dir_name, os.path.basename(cp_entry))
                    if not os.path.isfile(new_jar_name):
                        shutil.copyfile(cp_entry, new_jar_name)
                    clean_cp.append(new_jar_name)
                else:
                    clean_cp.append(cp_entry)
                pass
            else:
                #todo what happens here?
                clean_cp.append(cp_entry)

        randoop_cmd = ['java', '-ea', '-classpath', os.pathsep.join(clean_cp), 
                "randoop.main.Main", "gentests", "--classlist=%s"%class_files_file_name,
                "--timelimit=60", "--silently-ignore-bad-class-names=true",
                "--junit-output-dir=%s"%out_dir_name]

        junit_cp = list(clean_cp)
        junit_cp.append(junit_jar)
        junit_build_cmd = ['javac', '-classpath', os.pathsep.join(junit_cp), os.path.join(out_dir_name, 'RandoopTest*.java'), '-d', out_dir_name]

        junit_run_cp = list(junit_cp)
        junit_run_cp.append(hamcrest_jar)
        junit_run_cp.append(out_dir_name)

        junit_run_cmd = ['java', '-classpath', os.pathsep.join(junit_run_cp), "org.junit.runner.JUnitCore", 'RandoopTest']

        bash_script_name = "run_randoop_%04d.sh" % (i)
        with open(bash_script_name, mode='w') as myfile:
            myfile.write("#!/bin/bash\n")
            myfile.write("echo \"Run Randoop\"\n")
            myfile.write(" ".join(randoop_cmd))
            myfile.write("\n")
            myfile.write("echo \"Build tests\"\n")
            myfile.write(" ".join(junit_build_cmd))
            myfile.write("\n")
            myfile.write("echo \"Run tests\"\n")
            myfile.write(" ".join(junit_run_cmd))
            myfile.write("\n")
        print("Written script to %s" % bash_script_name)

        i += 1

def get_qualified_class_name_from_file(class_file_name, class_file_path):
    """ terrible hack for now """
    suffix = class_file_name.replace(class_file_path+os.sep, "")
    mid_section = suffix.replace(".class", "")
    return mid_section.replace(os.sep, ".")


def find_or_download_jars():
    '''
        Finds or downloads the randoop, junit, and hamrest jars.
    '''
    randoop_jar_dir = os.path.join(os.getcwd(), '__randoop_files')
    if not os.path.isdir(randoop_jar_dir):
        os.makedirs(randoop_jar_dir)

    randoop_jar = os.path.join(randoop_jar_dir, "randoop-2.0.jar")
    if not os.path.isfile(randoop_jar):
        print("Downloading randoop to %s" % randoop_jar)
        urllib.request.urlretrieve ("https://github.com/randoop/randoop/releases/download/v2.0/randoop-2.0.jar", randoop_jar)

    junit_jar = os.path.join(randoop_jar_dir, "junit-4.12.jar")
    if not os.path.isfile(junit_jar):
        print("Downloading junit to %s" % junit_jar)
        urllib.request.urlretrieve ("https://github.com/junit-team/junit/releases/download/r4.12/junit-4.12.jar", junit_jar)

    hamcrest_jar = os.path.join(randoop_jar_dir, "hamcrest-core-1.3.jar")
    if not os.path.isfile(hamcrest_jar):
        print("Downloading hamcrest to %s" % hamcrest_jar)
        urllib.request.urlretrieve ("http://search.maven.org/remotecontent?filepath=org/hamcrest/hamcrest-core/1.3/hamcrest-core-1.3.jar", hamcrest_jar)

    return (randoop_jar, junit_jar, hamcrest_jar)








