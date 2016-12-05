import os
import util
import zipfile
import timeit
import do_like_javac.tools.common as cmdtools

def is_switch(s):
    return s != None and s.startswith('-')

def get_entry_point(jar):
    class_pattern = "Main-Class:"

    with zipfile.ZipFile(jar, 'r') as zip:
        metadata = str.splitlines(zip.read("META-INF/MANIFEST.MF"))
        for line in metadata:
            if class_pattern in line:
                content = line[len(class_pattern):].strip()
                return {"jar": jar, "main": content}

    return {"jar": jar}

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
        build_output = util.get_build_output(self.build_cmd)
        stats['build_time'] = timeit.default_timer() - start_time

        with open(os.path.join(self.args.output_directory, 'build_output.txt'), 'w') as f:
            f.write(build_output)

        build_lines = build_output.split('\n')

        javac_commands = self.get_javac_commands(build_lines)
        target_jars = self.get_target_jars(build_lines)
        jars_with_entry_points = map(get_entry_point, target_jars)

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

            if a.endswith('.java'):
                files.append(a)
                possible_switch_arg = False

            if is_switch(prev_arg):
                if possible_switch_arg:
                    switches[prev_arg[1:]] = a
                else:
                    switches[prev_arg[1:]] = True

            if is_switch(a):
                prev_arg = a
            else:
                prev_arg = None

        return dict(java_files=files, javac_switches=switches)

    def record_stats(self, stats, javac_commands, jars):
        stats['source_files'] = sum([len(cmd['java_files']) for cmd in javac_commands])
        stats['class_files'] = sum([len(cmdtools.get_classes(cmd)) for cmd in javac_commands])
        stats['javac_invocations'] = len(javac_commands)
        stats['built_jars'] = len(jars)
        stats['executable_jars'] = len([jar for jar in jars if 'main' in jar])
