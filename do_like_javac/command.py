import pprint
from . import arg
from . import log
from . import tools
from . import cache
import os,json,sys

def output_json(filename, obj):
    with open(filename, 'w') as f:
        f.write(json.dumps(obj,
                           sort_keys=True,
                           indent=4))

def main():
    args, cmd, capturer = arg.parse_args()

    log.configure_logging(args.output_directory, args.log_to_stderr)
    log.log_header()

    result = cache.retrieve(cmd, args, capturer)

    if not result:
        print("DLJC: Build command failed.")
        sys.exit(1)

    javac_commands, jars, stats = result
    if len(javac_commands) == 0:
        raise Exception("command.main: no javac commands found by capturer:\n  cmd = {}\n  args = {}".format(cmd, args))

    log.info('Results: %s', pprint.pformat(javac_commands))
    output_json(os.path.join(args.output_directory, 'javac.json'), javac_commands)
    output_json(os.path.join(args.output_directory, 'jars.json'), jars)
    output_json(os.path.join(args.output_directory, 'stats.json'), stats)

    tools.run(args, javac_commands, jars)
