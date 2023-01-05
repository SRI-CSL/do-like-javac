import json
import os
import pprint
import sys

from . import arg, cache, log, tools


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
    if not javac_commands or len(javac_commands) == 0:
        raise ValueError(f"no javac commands found by capturer:\n\tcmd = {cmd}\n\targs = {args}")

    log.info('Results: %s', pprint.pformat(javac_commands))
    output_json(os.path.join(args.output_directory, 'javac.json'), javac_commands)
    output_json(os.path.join(args.output_directory, 'jars.json'), jars)
    output_json(os.path.join(args.output_directory, 'stats.json'), stats)

    tools.run(args, javac_commands, jars)
