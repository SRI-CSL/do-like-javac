import logging
import os
import sys
import platform
import pprint
import subprocess
import traceback


def run_checker(javac_commands,args):
	# checker-framework javac.
	javacheck = os.environ['JSR308']+"/checker-framework/checker/bin/javac"
	checker_command = []
	checker_command.extend([javacheck])

	for jc in javac_commands:
		pprint.pformat(jc)
		javac_switches = jc['javac_switches']
		cp = javac_switches['classpath']
		java_files = ' '.join(jc['java_files'])
		cmd = checker_command + ["-processor", args.checker, "-classpath", cp, java_files]
		print ("Running %s" % cmd)
		try:
			print (subprocess.check_output(cmd, stderr=subprocess.STDOUT))
		except subprocess.CalledProcessError as e:
			print e.output
