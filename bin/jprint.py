import logging
import os
import sys
import platform
import pprint
import subprocess
import traceback

def run_printer(javac_commands, jars):
    pp = pprint.PrettyPrinter(indent=2)
    for jc in javac_commands:
        pp.pprint(jc)
        javac_switches = jc['javac_switches']
    print("Target JARs (experimental):")
    pp.pprint(jars)
