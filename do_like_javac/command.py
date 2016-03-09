import pprint
import arg
import log
import tools

def main():
    args, cmd, capturer = arg.parse_args()

    log.configure_logging(args.output_directory, args.log_to_stderr)
    log.log_header()

    javac_commands, jars = capturer.gen_instance(cmd).capture()

    log.info('Results: %s', pprint.pformat(javac_commands))

    tools.run(args, javac_commands, jars)
