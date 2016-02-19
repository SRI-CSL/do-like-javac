import util
import zipfile

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

class GenericCapture:
    def __init__(self, cmd):
        self.build_cmd = cmd

    def get_javac_commands(self, verbose_output):
        return []

    def get_target_jars(self, verbose_output):
        return []

    def capture(self):
        build_output = util.get_build_output(self.build_cmd)
        javac_commands = self.get_javac_commands(build_output)
        target_jars = self.get_target_jars(build_output)
        jars_with_entry_points = map(get_entry_point, target_jars)
        return [javac_commands, jars_with_entry_points]

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
