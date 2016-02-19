import logging
import os
import sys
import platform
import pprint
import subprocess
import traceback


def run_inference(javac_commands,args):

	# the dist directory if CFI.
	CFI_dist = os.environ['JSR308']+"/checker-framework-inference/dist"
	CFI_command = []
	
	CFI_command.extend(["java"])
	
	for jc in javac_commands:
		pprint.pformat(jc)
		javac_switches = jc['javac_switches']
		target_cp = javac_switches['classpath']
		java_files = ' '.join(jc['java_files'])
		cp = target_cp +":"+ CFI_dist + "/checker.jar:" + CFI_dist + "/plume.jar:" + \
		     CFI_dist + "/checker-framework-inference.jar"
		cmd = CFI_command + ["-classpath", cp, "checkers.inference.InferenceLauncher" , 
				     "--checker" ,args.checker, "--solver", args.solver , 
				     "--mode" , args.mode ,"--targetclasspath", target_cp, "-afud", args.afuOutputDir, java_files]
		print ("Running %s" % cmd)
		try:
			print (subprocess.check_output(cmd, stderr=subprocess.STDOUT))
		except:
			print ('calling {cmd} failed\n{trace}'.format(cmd=' '.join(cmd),trace=traceback.format_exc()))
