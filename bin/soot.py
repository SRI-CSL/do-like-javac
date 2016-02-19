import logging
import os
import sys
import platform
import pprint
import subprocess
import traceback


def run_soot(javac_commands):

	soot_jar = os.path.dirname(os.path.realpath(__file__))+"/../soot-trunk.jar"
	soot_command = []
	# first add the call to the soot jar.
	soot_command.extend(["java", "-jar", soot_jar])
	
	# now add the generic soot args that we want to use.
	# TODO: these should actually be parsed from command line.
	soot_command.extend(["-pp", "-src-prec", "c"])

	for jc in javac_commands:
		pprint.pformat(jc)
		#jc['java_files']
		javac_switches = jc['javac_switches']
		cp = javac_switches['classpath']
		class_dir = javac_switches['d']

		cmd = soot_command + ["-cp", cp, "-process-dir", class_dir]
		print ("Running %s" % cmd)
		try:
			print (subprocess.check_output(cmd, stderr=subprocess.STDOUT))
		except:
			print ('calling {cmd} failed\n{trace}'.format(cmd=' '.join(cmd),trace=traceback.format_exc()))


