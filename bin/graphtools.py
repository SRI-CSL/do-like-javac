import logging
import os
import sys
import platform
import pprint
import subprocess
import traceback


def run(javac_commands, args):
	run_tool(args.jar, javac_commands, args.output_directory)


def run_tool(jarfile, javac_commands, outdir):
	# first add the call to the soot jar.
	tool_command = []
	tool_command.extend(["java", "-jar", jarfile])
	
	pp = pprint.PrettyPrinter(indent=2)
	for jc in javac_commands:
		pp.pformat(jc)
		#jc['java_files']
		javac_switches = jc['javac_switches']		
		class_dir = os.path.abspath(javac_switches['d'])

		java_files = jc['java_files']
		java_files_file = os.path.join(os.getcwd(), '__java_file_names.txt')
		with open(java_files_file, 'w') as f:
			for s in java_files:
				f.write(s)
				f.write("\n")

		current_outdir = os.path.join(outdir, class_dir.replace(os.getcwd(),'').replace(os.sep,"_"))

		cmd = tool_command + ["-o", current_outdir, "-j", class_dir, "-source", java_files_file ]
		print ("Running %s" % ' '.join(cmd))
		try:
			print (subprocess.check_output(cmd, stderr=subprocess.STDOUT))
		except:
			print ('calling {cmd} failed\n{trace}'.format(cmd=' '.join(cmd),trace=traceback.format_exc()))


