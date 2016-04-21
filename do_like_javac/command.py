import pprint
import arg
import log
import tools
import cache

def main():
    args, cmd, capturer = arg.parse_args()

    log.configure_logging(args.output_directory, args.log_to_stderr)
    log.log_header()

    javac_commands, jars = cache.retrieve(cmd, args, capturer)

    log.info('Results: %s', pprint.pformat(javac_commands))

    tools.run(args, javac_commands, jars)
