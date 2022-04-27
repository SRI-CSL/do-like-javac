from __future__ import annotations

import os
import typing as ty
from abc import ABC, abstractmethod

from . import common

class LineProcessor(ABC):
  subclasses = []
  
  def __init_subclass__(cls, **kwargs):
    super().__init_subclass__(**kwargs)
    cls.subclasses.append(cls)
  
  @abstractmethod
  def process(txt: str) -> ty.Optional[str]:
    pass

class RandoopVersion(LineProcessor):
  def process(txt: str) -> ty.Optional[str]:
    if not txt.startswith('Randoop for Java version'): # VERSION
      return None
    info_arr = txt[txt.index("\"") + 1, txt.rindex("\"")].split(",")
    local_changes = 'NONE' if not info_arr[1] or '' ==  info_arr[1] else info_arr[1].split()[0].strip()
    
    qualdata, metadata = {}, {}
    qualdata["RANDOOP_VERSION"] = info_arr[0]
    qualdata["DATE"] = info_arr[4].trim()
    metadata["CHANGES"] = local_changes
    metadata["BRANCH"] = info_arr[2].trim().split(" ")[1].trim()
    metadata["COMMIT"] = info_arr[3].trim().split(" ")[1].trim()
    
    return {
      "RANDOOP_TOOL_QUALIFICATION" : qualdata, 
      "RANDOOP_TESTS_AND_METRICS": metadata}
  
class ExploredClasses(LineProcessor):
  def process(txt: str) -> ty.Optional[str]:
    # if (!text.startsWith(EXPLORED_CLASSES)) return Optional.empty();
    if not txt.startswith('Will explore'):
      return None
    metadata = {}
    info_array = txt.split()
    metadata['EXPLORED_CLASSES'] = info_array[2].trim()
    return {"RANDOOP_TESTS_AND_METRICS": metadata}

class PublicMembers(LineProcessor):
  def process(txt: str) -> ty.Optional[str]:
    if not txt.startswith("PUBLIC MEMBERS"):
      return None
    metadata = {}
    info_array = txt.split("=")
    metadata['PUBLIC_MEMBERS'] = info_array[1].trim()
    return {"RANDOOP_TESTS_AND_METRICS": metadata}

class NormalExec(LineProcessor):
  def process(txt: str) -> ty.Optional[str]:
    if not txt.startswith("Normal method executions"):
      return None
    metadata = {}
    info_array = txt.split(":")
    metadata['NORMAL_EXECUTIONS'] = info_array[1].trim()
    return {"RANDOOP_TESTS_AND_METRICS": metadata}

class ExceptionalExec(LineProcessor):
  def process(txt: str) -> ty.Optional[str]:
    if not txt.startswith("Exceptional method executions"):
      return None
    metadata = {}
    info_array = txt.split(":")
    metadata['EXCEPTIONAL_EXECUTIONS'] = info_array[1].trim()
    return {"RANDOOP_TESTS_AND_METRICS": metadata}

class NormalTermination(LineProcessor):
  def process(txt: str) -> ty.Optional[str]:
    if not txt.startswith("Average method execution time (normal termination)"):
      return None
    metadata = {}
    info_array = txt.split(":")
    metadata['AVG_NORMAL_TERMINATION_TIME'] = info_array[1].trim()
    return {"RANDOOP_TESTS_AND_METRICS": metadata}

class ExceptionalTermination(LineProcessor):
  def process(txt: str) -> ty.Optional[str]:
    if not txt.startswith("Average method execution time (exceptional termination)"):
      return None
    metadata = {}
    info_array = txt.split(":")
    metadata['AVG_EXCEPTIONAL_TERMINATION_TIME'] = info_array[1].trim()
    return {"RANDOOP_TESTS_AND_METRICS": metadata}

class MemoryUsage(LineProcessor):
  def process(txt: str) -> ty.Optional[str]:
    if not txt.startswith("Approximate memory usage"):
      return None
    metadata = {}
    info_array = txt.split()
    metadata['MEMORY_USAGE'] = info_array[3].trim()
    return {"RANDOOP_TESTS_AND_METRICS": metadata}

class RegressionTestCount(LineProcessor):
  def process(txt: str) -> ty.Optional[str]:
    if not txt.startswith("Regression test count"):
      return None
    metadata = {}
    info_array = txt.split(":")
    metadata['REGRESSION_TEST_COUNT'] = info_array[1].trim()
    return {"RANDOOP_TESTS_AND_METRICS": metadata}
  
class ErrorRevealingTestCount(LineProcessor):
  def process(txt: str) -> ty.Optional[str]:
    if not txt.startswith("Error-revealing test count"):
      return None
    metadata = {}
    info_array = txt.split(":")
    metadata['ERROR_REVEALING_TEST_COUNT'] = info_array[1].trim()
    return {"RANDOOP_TESTS_AND_METRICS": metadata}

class InvalidTestCount(LineProcessor):
  def process(txt: str) -> ty.Optional[str]:
    if not txt.startswith("Invalid tests generated"):
      return None
    metadata = {}
    info_array = txt.split(":")
    metadata['INVALID_TESTS_GENERATED'] = info_array[1].trim()
    return {"RANDOOP_TESTS_AND_METRICS": metadata}

def processline(line: str) -> dict:
  for each_proc in LineProcessor.subclasses:
    out = each_proc.process(line)
    if out or len(out) > 0:
      return out

  return None

def generate_json_randoop_evidence(args, tool_stats, out_dir):
  randoop_log_file = os.path.join(out_dir, "randoop-log.txt")

  if not os.path.exists(randoop_log_file):
    return None

  try:
    f = open(randoop_log_file, 'r')
  except OSError:
    common.log(args, 'descert', f'Failed to read {randoop_log_file}')

  evidence = {}
  # Randoop tool config
  evidence['RANDOOP_JUNIT_TEST_GENERATION'] = {}
  evidence['RANDOOP_JUNIT_TEST_GENERATION']['INVOKEDBY'] = 'do-like-javac'
  evidence['RANDOOP_JUNIT_TEST_GENERATION']['AUTOMATEDBY'] = 'do-like-javac'
  evidence['RANDOOP_JUNIT_TEST_GENERATION']['PARAMETERS'] = tool_stats['gen_stats']['cmd_args']

  # qualification data
  evidence['RANDOOP_TOOL_QUALIFICATION'] = {}
  evidence['RANDOOP_TOOL_QUALIFICATION']['TITLE'] = 'do-like-javac'
  evidence['RANDOOP_TOOL_QUALIFICATION']['SUMMARY'] = 'Runs Randoop via do-like-javac'
  evidence['RANDOOP_TOOL_QUALIFICATION']['QUALIFIEDBY'] = 'SRI International'
  evidence['RANDOOP_TOOL_QUALIFICATION']['USERGUIDE'] = 'https://raw.githubusercontent.com/SRI-CSL/do-like-javac/master/README.md'
  evidence['RANDOOP_TOOL_QUALIFICATION']['INSTALLATION'] = 'https://raw.githubusercontent.com/SRI-CSL/do-like-javac/master/README.md'
  evidence['RANDOOP_TOOL_QUALIFICATION']['ACTIVITY'] = 'TestGeneration'

  evidence['RANDOOP_TESTS_AND_METRICS'] = {}
  with f:
    for line in f:
      out_dict = processline(line)
      if out_dict is not None:
        for key in out_dict:
          if key == 'RANDOOP_TOOL_QUALIFICATION':
            evidence['RANDOOP_TOOL_QUALIFICATION'].update(out_dict[key])
          else:
            # metrics metrics
            evidence['RANDOOP_TESTS_AND_METRICS'].update(out_dict[key])

  evidence['RANDOOP_TESTS_AND_METRICS']['TEST_GENERATION_TIME'] = tool_stats['gen_stats']['time']
  evidence['RANDOOP_TESTS_AND_METRICS']['TEST_COMPILATION_TIME'] = tool_stats['comp_stats']['time']

  return evidence

def generate_json_daikon_evidence(args, tool_stats, out_dir):
  pass

