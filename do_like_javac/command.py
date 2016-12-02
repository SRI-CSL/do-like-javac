import pprint
import arg
import log
import tools
import cache
import os,json

def output_json(filename, obj):
    with open(filename, 'w') as f:
        f.write(json.dumps(obj,
                           sort_keys=True,
                           indent=4))

def main():
    args, cmd, capturer = arg.parse_args()

    log.configure_logging(args.output_directory, args.log_to_stderr)
    log.log_header()

    javac_commands, jars, stats = cache.retrieve(cmd, args, capturer)

    log.info('Results: %s', pprint.pformat(javac_commands))
    output_json(os.path.join(args.output_directory, 'javac.json'), javac_commands)
    output_json(os.path.join(args.output_directory, 'jars.json'), jars)
    output_json(os.path.join(args.output_directory, 'stats.json'), stats)

    tools.run(args, javac_commands, jars)
