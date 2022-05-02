from __future__ import annotations

import json
import os
import typing as ty
from abc import ABC, abstractmethod
from datetime import date

from . import common, jsoninv


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

def generate_qual_data(tool:str, activity: str, summary: str, readme_url: str) -> dict:
  tool = tool.upper()
  qual_evidence = {}
  qual_evidence[f'{tool}_TOOL_QUALIFICATION'] = {}
  qual_evidence[f'{tool}_TOOL_QUALIFICATION']['TITLE'] = tool.capitalize()
  qual_evidence[f'{tool}_TOOL_QUALIFICATION']['SUMMARY'] = summary
  qual_evidence[f'{tool}_TOOL_QUALIFICATION']['QUALIFIEDBY'] = 'SRI International'
  qual_evidence[f'{tool}_TOOL_QUALIFICATION']['USERGUIDE'] = readme_url
  qual_evidence[f'{tool}_TOOL_QUALIFICATION']['INSTALLATION'] = readme_url
  qual_evidence[f'{tool}_TOOL_QUALIFICATION']['ACTIVITY'] = activity
  qual_evidence[f'{tool}_TOOL_QUALIFICATION']['DATE'] = date.today()
  return qual_evidence

def get_test_driver_class(driver, out_dir):  
  for root, _, files in os.walk(out_dir):
    for file in files:
      if file.endswith('.class'):
        if driver in file:
          driver_class_file = os.path.join(root, file)
          return driver_class_file

  return None

def get_dljc_kwargs(args):
  dljc_kwargs = []
  if args and len(vars(args)) > 0:
    dljc_kwargs += [f"{k}:'{vars(args)[k]}'" for k in vars(args)]
  return dljc_kwargs

def generate_json_randoop_evidence(args, tool_stats):
  randoop_log_file = os.path.join("dljc-out", "randoop-log.txt")

  if not os.path.exists(randoop_log_file):
    return None

  try:
    f = open(randoop_log_file, 'r')
  except OSError:
    common.log(args, 'descert', f'Failed to read {randoop_log_file}')

  evidence = {}
  # Randoop qualification data
  evidence.update(generate_qual_data(
    'randoop', 'TestGeneration', 'Automatic unit test generation for Java', 
    'https://randoop.github.io/randoop/manual/index.html'))
  
  # Randoop tool config
  evidence['RANDOOP_JUNIT_TEST_GENERATION'] = {}
  evidence['RANDOOP_JUNIT_TEST_GENERATION']['INVOKEDBY'] = 'do-like-javac (dljc)'
  evidence['RANDOOP_JUNIT_TEST_GENERATION']['AUTOMATEDBY'] = 'do-like-javac (dljc)'
  evidence['RANDOOP_JUNIT_TEST_GENERATION']['PARAMETERS'] = [
    {'randoop': tool_stats['randoop']['gen_stats']['cmd_args']}]
  
  dljc_kwargs = get_dljc_kwargs(args)
  if dljc_kwargs or len(dljc_kwargs) > 0:
    evidence['RANDOOP_JUNIT_TEST_GENERATION']['PARAMETERS'] += [{'dljc':' '.join(dljc_kwargs)}]

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

  evidence['RANDOOP_TESTS_AND_METRICS']['TEST_GENERATION_TIME'] = tool_stats['randoop']['gen_stats']['time']
  evidence['RANDOOP_TESTS_AND_METRICS']['TEST_COMPILATION_TIME'] = tool_stats['randoop']['comp_stats']['time']
  evidence['RANDOOP_TESTS_AND_METRICS']['GENERATED_TEST_FILES'] = tool_stats['randoop']['gen_stats']['files_to_compile']

  return {'Evidence': evidence}

def generate_json_daikon_evidence(args, tool_stats, out_dir):
  evidence = {}
  # qualification data
  evidence.update(generate_qual_data(
    'daikon', 'Dynamic Analysis', 'Dynamic detection of likely program invariants',
    'http://plse.cs.washington.edu/daikon/download/doc/daikon.html'))

  # Daikon tool config
  evidence['DAIKON_LIKELY_INVS_DETECTION'] = {}
  evidence['DAIKON_LIKELY_INVS_DETECTION']['INVOKEDBY'] = 'do-like-javac (dljc)'
  evidence['DAIKON_LIKELY_INVS_DETECTION']['AUTOMATEDBY'] = 'do-like-javac (dljc)'
  evidence['DAIKON_LIKELY_INVS_DETECTION']['PARAMETERS'] = []
  evidence['DAIKON_LIKELY_INVS_DETECTION']['PARAMETERS'] += [{'dycomp': tool_stats['daikon']['dyncomp_stats']['cmd_args']}]
  evidence['DAIKON_LIKELY_INVS_DETECTION']['PARAMETERS'] += [{'chicory': tool_stats['daikon']['chicory_stats']['cmd_args']}]
  evidence['DAIKON_LIKELY_INVS_DETECTION']['PARAMETERS'] += [{'daikon': tool_stats['daikon']['daikon_stats']['cmd_args']}]
  
  dljc_kwargs = get_dljc_kwargs(args)
  if dljc_kwargs or len(dljc_kwargs) > 0:
    evidence['DAIKON_LIKELY_INVS_DETECTION']['PARAMETERS'] += [{'dljc':' '.join(dljc_kwargs)}]

  # metrics
  evidence['DAIKON_INVS_AND_METRICS'] = {}
  evidence['DAIKON_INVS_AND_METRICS']['DYCOMP_ELAPSED_TIME'] = tool_stats['daikon']['dyncomp_stats']['time']
  evidence['DAIKON_INVS_AND_METRICS']['CHICORY_ELAPSED_TIME'] = tool_stats['daikon']['chicory_stats']['time']
  evidence['DAIKON_INVS_AND_METRICS']['DAIKON_ELAPSED_TIME'] = tool_stats['daikon']['daikon_stats']['time']

  tree = jsoninv.parse_invariants_xml(args, out_dir)
  ppt_count, cls_count = 0, 0
  if tree or tree is not None:
    ppts = [ppt for ppt in tree.getroot()]
    ppt_count = len(ppts)
    cls_count = len({jsoninv.ppt_info(ppt)[0] for ppt in ppts})
  evidence['DAIKON_INVS_AND_METRICS']['PPT_COUNT'] = ppt_count
  evidence['DAIKON_INVS_AND_METRICS']['CLASSES_COUNT'] = cls_count

  daikon_invariants_file = os.path.join(out_dir, 'invariants.json')
  if not os.path.exists(daikon_invariants_file):
    common.log(args, 'descert', f'Failed to locate {daikon_invariants_file}')
    daikon_invariants_file = 'MISSING'
  evidence['DAIKON_INVS_AND_METRICS']['INVS_FILE'] = daikon_invariants_file

  try:
    f = open(daikon_invariants_file, 'r')
  except OSError:
    common.log(args, 'descert', f'Failed to read {daikon_invariants_file}')

  invariants_data = json.loads(f.read())
  evidence['DAIKON_INVS_AND_METRICS']['INVARIANTS_COUNT'] = len(invariants_data["invariants"])

  randoop_driver = "ErrorTestDriver" if args.error_driver else "RegressionTestDriver"
  supporting_files = []
  if daikon_invariants_file != 'MISSING':
    # if the daikon invs file exists then its xml, dtrace, gz counterparts must also exist
    supporting_files += [os.path.join(out_dir, 'invariants.xml')]
    supporting_files += [os.path.join(out_dir, "invariants.gz")]
    supporting_files += [os.path.join(out_dir, f"{randoop_driver}.dtrace.gz")]
    supporting_files += [os.path.join(out_dir, f"{randoop_driver}.decls-DynComp")]
  evidence['DAIKON_INVS_AND_METRICS']['SUPPORT_FILES'] = supporting_files
  driver_class_file = get_test_driver_class(randoop_driver, out_dir)
  evidence['DAIKON_INVS_AND_METRICS']['TEST_DRIVER'] = driver_class_file if driver_class_file is not None else 'MISSING'

  return {'Evidence': evidence}

