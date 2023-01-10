import os
import timeit
import zipfile

import do_like_javac.tools.common as cmdtools


def is_switch(s):
    return s != None and s.startswith('-')
def is_switch_first_part(s):
    return s != None and s.startswith('-') and ("=" not in s)

## brought this from github.com/kelloggm/do-like-javac
def is_switch_first_part(s):
    return s != None and s.startswith('-') and ("=" not in s)

def get_entry_point(jar):
    class_pattern = "Main-Class:"

    with zipfile.ZipFile(jar, 'r') as zip:
        metadata = []
        try:
            metadata = str.splitlines(zip.read("META-INF/MANIFEST.MF").decode("utf-8"))
        except TypeError as e:
            print(f"ERROR: unable to read META-INF/MANIFEST.MF. See: {e}")
        for line in metadata:
            if class_pattern in line:
                content = line[len(class_pattern):].strip()
                return {"jar": jar, "main": content}

    return {"jar": jar}

def ignore_path(path):
    return \
        not path \
        or 'generated-sources' in path

def guess_source(switches):
    """If no .java files are detected and --guess has been passed on the
    command line, this will attempt to fill in the blanks based on the
    -sourcepath option to javac."""

    sourcepath = switches.get('sourcepath')
    files = []

    if not sourcepath:
        return []

    paths = [path for path in sourcepath.split(':')
             if not ignore_path(path)]

    for path in paths:
        for dirname, subdirs, dirfiles in os.walk(path):
            files.extend([os.path.join(dirname, file) for file in dirfiles
                          if file.endswith('.java')])

    return files

class GenericCapture(object):
    def __init__(self, cmd, args):
        self.build_cmd = cmd
        self.args = args

    def get_javac_commands(self, verbose_output):
        return []

    def get_target_jars(self, verbose_output):
        return []

    def capture(self):
        stats = {}

        start_time = timeit.default_timer()
        result = cmdtools.run_cmd(self.build_cmd, self.args)
        # stats['build_time'] = result['time']
        stats['build_time'] = timeit.default_timer() - start_time

        build_out_file = os.path.join(self.args.output_directory, 'build_output.txt')
        with open(build_out_file, 'w') as f:
            f.write(result['output'])

        if result['return_code'] != 0:
            return None

        build_lines = result['output'].split('\n')

        javac_commands = self.get_javac_commands(build_lines)
        target_jars = self.get_target_jars(build_lines)
        jars_with_entry_points = list(map(get_entry_point, target_jars))

        self.record_stats(stats, javac_commands, jars_with_entry_points)

        return [javac_commands, jars_with_entry_points, stats]

    def javac_parse(self, javac_command):
        files = []
        switches = {}

        prev_arg = None

        for a in javac_command:
            possible_switch_arg = True

            if is_switch(a):
                possible_switch_arg = False
            elif a.endswith('.java'):
                files.append(a)
                possible_switch_arg = False

            if is_switch_first_part(prev_arg):
                if possible_switch_arg:
                    switches[prev_arg[1:]] = a
                else:
                    switches[prev_arg[1:]] = True

            if is_switch(a):
                prev_arg = a
            else:
                prev_arg = None

        if self.args.guess_source and not files:
            files = guess_source(switches)

        return dict(java_files=files, javac_switches=switches)

    def record_stats(self, stats, javac_commands, jars):
        stats['source_files'] = sum([len(cmd['java_files']) for cmd in javac_commands])
        stats['class_files'] = sum([len(cmdtools.get_class_files(cmd)) for cmd in javac_commands])
        stats['javac_invocations'] = len(javac_commands)
        stats['built_jars'] = len(jars)
        stats['executable_jars'] = len([jar for jar in jars if 'main' in jar])
