import argparse
import itertools
import json
import os
import re
import shutil
import typing as ty
from dataclasses import dataclass, replace
from datetime import date, datetime

from dataclass_csv import DataclassWriter, dateformat

from . import common

argparser = argparse.ArgumentParser(add_help=False)
csve_group = argparser.add_argument_group('csve arguments')

csve_group.add_argument(
  '--override-evidence',
  action='store_true',
  dest='override_evidence',
  help='Overrides csv evidence files')


@dataclass(frozen=True)
class BasicData:
  qual_title: str
  version: str
  summary: str
  description: str
  
  def doc_id(self) -> str:
    return '_'.join(self.version.split('.'))
  
  def identifier(self) -> str:
    return f'{self.qual_title}_{self.doc_id()}'
  
  def title(self) -> str:
    return f'{self.qual_title} version {self.version}'
  
  def user_guide_id(self) -> str:
    return f'DOCUMENT_{self.qual_title.upper()} version {self.doc_id()}'


@dataclass(frozen=True)
@dateformat("%Y-%m-%dT%H:%M:%S.%f%z")
class GeneralData:
  identifier: str = ''
  description: str = ''
  generatedBy_identifier: str = ''
  generatedWith_identifier: str = ''
  generationConfiguration_identifier: str = ''
  generatedAtTime: datetime = None

@dataclass(frozen=True)
class ToolData:
  # RACK 10.2
  toolInstallationConfiguration_identifier: str = ''
  toolUsageSummary: str = ''
  toolVersion: str = ''
  description: str = ''
  identifier: str = ''
  title: str = ''
  userGuide_identifier: str = ''

@dataclass(frozen=True)
@dateformat("%Y-%m-%dT%H:%M:%S.%f%z")
class ToolInvokeData:
  # RACK 10.2
  # aka ToolConfigurationInstance
  # Runs {Tool} with paramters [....] 
  description: str = ''
  generatedAtTime: datetime = None
  identifier: str = ''
  title: str = ''

@dataclass(frozen=True)
@dateformat("%Y-%m-%dT%H:%M:%S.%f%z")
class FileData:
  # RACK 10.2
  filename: str = ''
  description: str = ''
  generatedAtTime: datetime = None
  identifier: str = ''
  title: str = ''
  fileFormat_identifier: str = ''
  wasGeneratedBy_identifier: str = ''

@dataclass(frozen=True)
@dateformat("%Y-%m-%dT%H:%M:%S.%f%z")
class RandoopMetricData:
  numberOfErrorRevealingTestCases: int = 0
  numberOfReducedViolationInducingTestCases: int = 0
  numberOfRegressionTestCases: int = 0
  numberOfViolationInducingTestCases: int = 0
  # Note: explicitly defined given that a method named `totalNumberOfTestCases` 
  # which returns numberOfErrorRevealingTestCases + numberOfRegressionTestCases 
  # is not written as a column in a csv file.
  totalNumberOfTestCases: int = 0
  description: str = ''
  generatedAtTime: datetime = None
  identifier: str = ''
  title: str = ''
  jUnitTestFile_identifier: str = ''
  producedBy_identifier: str = ''
  verifies_identifier: str = ''
  definedIn_identifier: str = ''
  dataInsertedBy_identifier: str = ''
  wasAttributedTo_identifier: str = ''
  wasDerivedFrom_identifier: str = ''
  wasGeneratedBy_identifier: str = ''
  wasImpactedBy_identifier: str = ''
  asRevisionOf_identifier: str = ''

@dataclass(frozen=True)
@dateformat("%Y-%m-%dT%H:%M:%S.%f%z")
class ToolOutputData:
  # RACK 10.2
  description: str = ''
  endedAtTime: datetime = None
  identifier: str = ''
  startedAtTime: datetime = None
  title: str = ''
  wasInformedBy_identifier: str = ''
  testGenInfo_identifier: str = ''
  # toolInvocation_identifier: str = ''
  testGenInput_identifier: str = ''


@dataclass(frozen=True)
@dateformat("%Y-%m-%dT%H:%M:%S.%f%z")
class DocData:
  dateOfIssue: datetime = None
  versionNumber: str = ''
  description: str = ''
  generatedAtTime: datetime = None
  identifier: str = ''
  invalidatedAtTime: datetime = None
  title: str = ''
  approvalAuthority_identifier: str = ''
  issuingOrganization_identifier: str = ''
  references_identifier: str = ''
  status_identifier: str = ''
  definedIn_identifier: str = ''
  content_identifier: str = ''
  dataInsertedBy_identifier: str = ''
  wasAttributedTo_identifier: str = ''
  wasDerivedFrom_identifier: str = ''
  wasGeneratedBy_identifier: str = ''
  wasImpactedBy_identifier: str = ''
  wasRevisionOf_identifier: str = ''
  
@dataclass(frozen=True)
@dateformat("%Y-%m-%dT%H:%M:%S.%f%z")
class DaikonInvsData:
  classesCount: int = 0
  invariantCount: int = 0
  testsCount: int = 0
  description: str = ''
  generatedAtTime: datetime = None
  identifier: str = ''
  invalidatedAtTime: str = ''
  title: str = ''
  likelyInvariants_identifier: str = ''
  producedBy_identifier: str = ''
  supportFiles_identifier: str = ''
  testDriver_identifier: str = ''
  verifies_identifier: str = ''
  definedIn_identifier: str = ''
  dataInsertedBy_identifier: str = ''
  wasAttributedTo_identifier: str = ''
  wasDerivedFrom_identifier: str = ''
  wasGeneratedBy_identifier: str = ''
  wasImpactedBy_identifier: str = ''
  wasRevisionOf_identifier: str = ''

@dataclass(frozen=True)
@dateformat("%Y-%m-%dT%H:%M:%S.%f%z")
class LikelyProgramInvariant:
  invariantSpecification: str = ''
  description: str = ''
  generatedAtTime: datetime = None
  identifier: str = ''
  invalidatedAtTime: datetime = None
  title: str = ''
  definedIn_identifier: str = ''
  models_identifier: str = ''
  dataInsertedBy_identifier: str = ''
  wasAttributedTo_identifier: str = ''
  wasDerivedFrom_identifier: str = ''
  wasGeneratedBy_identifier: str = ''
  wasImpactedBy_identifier: str = ''
  wasRevisionOf_identifier: str = ''

def run(args, javac_commands, jars):
  out_dir = os.path.basename(args.output_directory)
  for jc in javac_commands:
    evidence_print_csv(args, jc, out_dir)

def get_test_class_directory(d, out_dir, iter_limit: int = 10) -> ty.Optional[str]:
  i = 1
  dirformat = "{}{}"
  
  if os.path.exists(os.path.join(out_dir, d)):
    return os.path.join(out_dir, d)

  while not os.path.exists(os.path.join(out_dir, dirformat.format(d, i))) and i < iter_limit:
    i += 1

  return os.path.join(out_dir, dirformat.format(d, i))

def move(src, dst):
  if os.path.exists(src):
    shutil.move(src, dst)

def rotate_and_make_dir(d):
  i = 1
  dirformat = "{}.{}"

  while os.path.exists(dirformat.format(d, i)):
    i += 1

  rd = dirformat.format(d, i)
  move(d, rd)
  os.mkdir(d)

def rmdir(dir_path):
  try:
    if os.path.isdir(dir_path):
      shutil.rmtree(dir_path)
  except OSError as e:
    print("Error: %s : %s" % (dir_path, e.strerror))

def evidence_print_csv(args, java_command, out_dir):
  test_class_directory = get_test_class_directory('test-classes', out_dir)
  if not os.path.exists(test_class_directory):
    common.log(args, 'csve', f'Failed to locate {test_class_directory}')
    return
  
  evidence_directory = os.path.join(out_dir, "evidence")
  if not os.path.exists(evidence_directory):
    os.mkdir(evidence_directory)
  else:
    if args.override_evidence:
      rmdir(evidence_directory)
    else:
      # rotate existing evidence directory
      rotate_and_make_dir(evidence_directory)
  
  randoop_evidence_json = os.path.join(test_class_directory, 'randoop-evidence.json')
  daikon_evidence_json = os.path.join(test_class_directory, 'daikon-evidence.json')

  # from *_evidence_json to *_evidence_csv
  randoop_print_csv(args, randoop_evidence_json, out_dir)
  daikon_print_csv(args, daikon_evidence_json, out_dir)


def camel_to_snake(name):
  name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
  return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name)

def get_basic_tool_info(tool:str, tool_data: dict) -> BasicData:
  tool_upper = tool.upper()
  tool_title = tool_data['Evidence'][f"{tool_upper}_TOOL_QUALIFICATION"]["TITLE"]
  tool_version = tool_data['Evidence'][f"{tool_upper}_TOOL_QUALIFICATION"][f"{tool_upper}_VERSION"]
  tool_summary = tool_data['Evidence'][f"{tool_upper}_TOOL_QUALIFICATION"]["SUMMARY"]
  
  return BasicData(
    qual_title=tool_title,
    version=tool_version,
    summary=tool_summary,
    description=f'Run {tool.capitalize()} using do-like-javac')

def get_invariants(tool_identifier: str, out_dir: str) -> ty.List[LikelyProgramInvariant]:
  invs = []
  with open(os.path.join(out_dir, 'invariants.json'), 'r') as f:
    program_invariants = json.load(f)['invariants']
    for program_invariant in program_invariants:
      postconds = program_invariant['postconds']
      preconds = program_invariant['preconds']
      params = ', '.join(program_invariant['params'])
      method_name = program_invariant['method']
      class_name = program_invariant['cls']

      descriptor = f"{class_name}.{method_name}({params})"
      inv_title = 'Likely program invariant specification'
      for (pos, pre) in itertools.zip_longest(postconds, preconds, fillvalue=None):
        if pos is not None:
          left, op, right = pos['left'], pos['op'], pos['right']
          pos_inv = LikelyProgramInvariant(
            invariantSpecification=f'{left} {op} {right}',
            description=f'post-condition in {descriptor}',
            identifier=f'LIKELY_INVARIANT_SPEC_{len(invs)}',
            title=inv_title)
          invs += [pos_inv]
        elif pre is not None:
          left, op, right = pos['left'], pos['op'], pos['right']
          pre_inv = LikelyProgramInvariant(
            invariantSpecification=f'{left} {op} {right}',
            description=f'pre-condition in {descriptor}',
            identifier=f'LIKELY_INVARIANT_SPEC_{len(invs)}',
            title=inv_title)
          invs += [pre_inv]
  return invs

def randoop_print_csv(args, randoop_evidence_json, out_dir):
  if not os.path.exists(randoop_evidence_json):
    common.log(args, 'csve', f'Failed to locate {randoop_evidence_json}')
    return
  try:
    rej = open(randoop_evidence_json, 'r')
  except OSError as o:
    common.log(args, 'csve', f'Failed to read {randoop_evidence_json}. See: {o}')
    return

  randoop_data = json.loads(rej.read())

  # collect tool data
  randoop_basic_data = get_basic_tool_info('randoop', randoop_data)
  evidence_directory = os.path.join(out_dir, "evidence")

  tool_data = ToolData(
    toolUsageSummary=randoop_basic_data.summary,
    toolVersion=randoop_basic_data.version,
    description=randoop_basic_data.description,
    identifier=randoop_basic_data.identifier(),
    title=randoop_basic_data.title(),
    userGuide_identifier=randoop_basic_data.user_guide_id())

  # 1. create evidence/ingest_DesCert_TOOL.csv
  ingest_tool_file = os.path.join(evidence_directory, "ingest_DesCert_TOOL.csv")
  with open(ingest_tool_file, "w") as f:
    try:
      w = DataclassWriter(f, [tool_data], ToolData)
      w.write()
    except Exception:
      common.log(args, 'csve', f'Failed to write {ingest_tool_file}')
      return
  
  # 1.1 create evidence/ingest_GenerationInformation.csv
  general_info_data = []
  general_info_data += [
    GeneralData(
      identifier=f"{randoop_basic_data.identifier()}_INVOKE_INFO",
      description='Info about invoking the Randoop Tool',
      generatedBy_identifier='Huascar_Sanchez',
      generatedWith_identifier=f"{randoop_basic_data.identifier()}",
      generationConfiguration_identifier=f"{randoop_basic_data.identifier()}_CONFIG_INSTANCE")]
  
  ingest_general_file = os.path.join(evidence_directory, "ingest_GenerationInformation.csv")
  with open(ingest_general_file, "w") as f:
    try:
      w = DataclassWriter(f, general_info_data, GeneralData)
      w.write()
    except Exception:
      common.log(args, 'csve', f'Failed to write {ingest_general_file}')
      return
  
  tests_creation_date = randoop_data['Evidence']["RANDOOP_TOOL_QUALIFICATION"]["DATE"]

  # collect tool invocation data
  tool_invoke_data = []
  randoop_params = randoop_data['Evidence']['RANDOOP_JUNIT_TEST_GENERATION']['PARAMETERS']
  for each_param_dict in randoop_params:
    tool_name = next(iter(each_param_dict))
    # DONT INCLUDE IT INVOKE CONFIG INSTANCE
    if tool_name == 'dljc':
      continue
    # Runs {Tool} with paramters [....] 
    tool_description = f'Runs {tool_name} with paramters {each_param_dict[tool_name]}'
    tool_identifier = f"{tool_name.upper()}_CONFIG_INSTANCE" if tool_name == 'dljc' else f"{randoop_basic_data.identifier()}_CONFIG_INSTANCE"
    tool_title = f'{tool_name.upper()} invocation paramters'
    tool_invoke = ToolInvokeData(
      description=tool_description,
      generatedAtTime=date.today(),
      identifier=tool_identifier,
      title=tool_title)
    tool_invoke_data += [tool_invoke]

  # 2. create evidence/ingest_Auto_ToolConfigurationInstance.csv
  ingest_tool_invoke_file = os.path.join(evidence_directory, "ingest_Auto_ToolConfigurationInstance.csv")
  with open(ingest_tool_invoke_file, "w") as f:
    try:
      w = DataclassWriter(f, tool_invoke_data, ToolInvokeData)
      w.write()
    except Exception:
      common.log(args, 'csve', f'Failed to write {ingest_tool_invoke_file}')
      return

  # collect tool metrics data
  numberOfErrorRevealingTestCases = int(randoop_data['Evidence']['RANDOOP_TESTS_AND_METRICS'].get('ERROR_REVEALING_TEST_COUNT', 0))
  numberOfRegressionTestCases = int(randoop_data['Evidence']['RANDOOP_TESTS_AND_METRICS'].get('REGRESSION_TEST_COUNT', 0))
  tool_metric_data = RandoopMetricData(
    numberOfErrorRevealingTestCases=numberOfErrorRevealingTestCases,
    numberOfReducedViolationInducingTestCases=0,
    numberOfRegressionTestCases=numberOfRegressionTestCases,
    numberOfViolationInducingTestCases=0,
    totalNumberOfTestCases=numberOfErrorRevealingTestCases + numberOfRegressionTestCases,
    description=f"{randoop_basic_data.title()} metrics",
    generatedAtTime=tests_creation_date,
    identifier=f"{randoop_basic_data.identifier()}_METRICS",
    title=f"{randoop_basic_data.title()} metrics data",
    wasGeneratedBy_identifier=randoop_basic_data.identifier())

  # collect file data
  tool_file_data = []
  tool_metrics_data = []
  generated_test_files = randoop_data['Evidence']['RANDOOP_TESTS_AND_METRICS']['GENERATED_TEST_FILES']
  for file_to_compile in generated_test_files:
    file_parts = os.path.splitext(file_to_compile)
    filename = os.path.basename(file_parts[0])
    filename_snake = camel_to_snake(filename)
    file_ext = file_parts[1].replace('.', '').upper()
    file_identifier = f"FILE_{filename_snake}".upper()
    file_data = FileData(
      filename=os.path.basename(file_to_compile),
      description='JUnit tests',
      generatedAtTime=tests_creation_date,
      identifier=file_identifier,
      title=filename_snake.replace('_', ' '),
      fileFormat_identifier=f'FORMAT_{file_ext}',
      wasGeneratedBy_identifier=randoop_basic_data.identifier())
    tool_file_data += [file_data]

    if "ErrorTestDriver" in filename:
      tool_metrics_data += [replace(
        tool_metric_data,
        numberOfRegressionTestCases=0,
        totalNumberOfTestCases=numberOfErrorRevealingTestCases,
        jUnitTestFile_identifier=file_identifier)]
    elif "RegressionTestDriver" in filename:
      tool_metrics_data += [replace(
        tool_metric_data,
        numberOfErrorRevealingTestCases=0,
        totalNumberOfTestCases=numberOfRegressionTestCases,
        jUnitTestFile_identifier=file_identifier)]

  manual_url = randoop_data['Evidence']["RANDOOP_TOOL_QUALIFICATION"]["USERGUIDE"]
  tool_file_data += [
    FileData(
      filename=manual_url,
      description=f'Randoop Manual {randoop_basic_data.version}',
      generatedAtTime=tests_creation_date,
      identifier=f'FILE_RANDOOP_{randoop_basic_data.doc_id()}',
      title=f'Randoop Manual {randoop_basic_data.version}',
      fileFormat_identifier='FORMAT_HTML',
      wasGeneratedBy_identifier='Michael_Ernst')]

  # 3. create evidence/ingest_Auto_FILE.csv
  ingest_file = os.path.join(evidence_directory, "ingest_Auto_FILE.csv")
  with open(ingest_file, "w") as f:
    try:
      w = DataclassWriter(f, tool_file_data, FileData)
      w.write()
    except Exception:
      common.log(args, 'csve', f'Failed to write {ingest_file}')
      return

  # 4. create evidence/ingest_Auto_RandoopTestsAndMetrics.csv
  ingest_metrics_file = os.path.join(evidence_directory, "ingest_Auto_RandoopTestsAndMetrics.csv")
  with open(ingest_metrics_file, "w") as f:
    try:
      w = DataclassWriter(f, tool_metrics_data, RandoopMetricData)
      w.write()
    except Exception:
      common.log(args, 'csve', f'Failed to write {ingest_metrics_file}')
      return

  # 5. create evidence/ingest_Auto_RandoopJUnitTestGeneration.csv
  junit_gen_data = ToolOutputData(
    description=f"{randoop_basic_data.title()} data",
    identifier=f"{randoop_basic_data.identifier()}_TEST",
    title=f"Tests generated by {randoop_basic_data.title()}",
    testGenInfo_identifier=f'{randoop_basic_data.identifier()}_INVOKE_INFO',
    testGenInput_identifier=randoop_basic_data.identifier())
  
  ingest_randoop_junit_file = os.path.join(evidence_directory, "ingest_Auto_RandoopJUnitTestGeneration.csv")
  with open(ingest_randoop_junit_file, "w") as f:
    try:
      w = DataclassWriter(f, [junit_gen_data], ToolOutputData)
      w.write()
    except Exception:
      common.log(args, 'csve', f'Failed to write {ingest_randoop_junit_file}')
      return

  # 6. create evidence/ingest_Auto_DOCUMENT.csv
  ingest_doc_file = os.path.join(evidence_directory, "ingest_Auto_DOCUMENT.csv")
  docs_data = [
    DocData(
      dateOfIssue=tests_creation_date,
      versionNumber=randoop_basic_data.version,
      description='Randoop Manual',
      identifier=f'DOCUMENT_RANDOOP_{randoop_basic_data.doc_id()}',
      title=f'Randoop Manual {randoop_basic_data.version}',
      approvalAuthority_identifier='ORG_UW',
      issuingOrganization_identifier='ORG_UW',
      content_identifier=f'FILE_RANDOOP_{randoop_basic_data.doc_id()}')]
  with open(ingest_doc_file, "w") as f:
    try:
      w = DataclassWriter(f, docs_data, DocData)
      w.write()
    except Exception:
      common.log(args, 'csve', f'Failed to write {ingest_doc_file}')
      return
  
  common.log(args, 'csve', f'Finished writing Randoop evidence data to {evidence_directory}')

def daikon_print_csv(args, daikon_evidence_json, out_dir):
  if not os.path.exists(daikon_evidence_json):
    common.log(args, 'csve', f'Failed to locate {daikon_evidence_json}')
    return
  try:
    dej = open(daikon_evidence_json, 'r')
  except OSError:
    common.log(args, 'csve', f'Failed to read {daikon_evidence_json}')
    return

  daikon_data = json.loads(dej.read())

  # collect tool data
  daikon_basic_data = get_basic_tool_info('daikon', daikon_data)

  evidence_directory = os.path.join(out_dir, "evidence")
  if not os.path.exists(evidence_directory):
    common.log(args, 'csve', f'Failed to find {evidence_directory} directory')
    return

  file_creation_date = daikon_basic_data['Evidence']['DAIKON_TOOL_QUALIFICATION']["DATE"]

  # 1. create evidence/ingest_DesCert_TOOL.csv
  tool_data = ToolData(
    toolUsageSummary=daikon_basic_data.summary,
    toolVersion=daikon_basic_data.version,
    description=daikon_basic_data.description,
    identifier=daikon_basic_data.identifier(),
    title=daikon_basic_data.title(),
    userGuide_identifier=daikon_basic_data.user_guide_id())

  ingest_tool_file = os.path.join(evidence_directory, "ingest_DesCert_TOOL.csv")
  with open(ingest_tool_file, 'a') as f:
    try:
      w = DataclassWriter(f, [tool_data], ToolData)
      w.write()
    except Exception:
      common.log(args, 'csve', f'Failed to write {ingest_tool_file}')
      return
    
  # 1.1 create evidence/ingest_GenerationInformation.csv
  general_info_data = []
  general_info_data += [
    GeneralData(
      identifier=f"{daikon_basic_data.identifier()}_INVOKE_INFO",
      description='Info about invoking the Daikon Tool',
      generatedBy_identifier='Huascar_Sanchez',
      generatedWith_identifier=f"{daikon_basic_data.identifier()}",
      generationConfiguration_identifier=f"{daikon_basic_data.identifier()}_CONFIG_INSTANCE")]
  
  ingest_general_file = os.path.join(evidence_directory, "ingest_GenerationInformation.csv")
  with open(ingest_general_file, "a") as f:
    try:
      w = DataclassWriter(f, general_info_data, GeneralData)
      w.write()
    except Exception:
      common.log(args, 'csve', f'Failed to write {ingest_general_file}')
      return

  # 2. update evidence/ingest_Auto_TOOL_INVOCATION_INSTANCE.csv
  tool_invoke_data = []
  daikon_params = daikon_basic_data['Evidence']['DAIKON_LIKELY_INVS_DETECTION']['PARAMETERS']
  for each_param_dict in daikon_params:
    tool_name = next(iter(each_param_dict))
    # don't include dljc info
    if tool_name == 'dljc':
      continue
    # Runs {Tool} with paramters [....] 
    tool_description = f'Runs {tool_name} with paramters {each_param_dict[tool_name]}'
    tool_identifier = f"{tool_name.upper()}_CONFIG_INSTANCE" if tool_name == 'dljc' else f"{daikon_basic_data.identifier()}_CONFIG_INSTANCE"
    tool_title = f'{tool_name.upper()} invocation paramters'
    tool_invoke = ToolInvokeData(
      description=tool_description,
      generatedAtTime=date.today(),
      identifier=tool_identifier,
      title=tool_title)
    tool_invoke_data += [tool_invoke]

  ingest_tool_invoke_file = os.path.join(evidence_directory, "ingest_Auto_ToolConfigurationInstance.csv")
  write_mode = "a" if os.path.exists(ingest_tool_invoke_file) else "w"
  with open(ingest_tool_invoke_file, write_mode) as f:
    try:
      w = DataclassWriter(f, tool_invoke_data, ToolInvokeData)
      w.write()
    except Exception:
      common.log(args, 'csve', f'Failed to write {ingest_tool_invoke_file}')
      return
  
  # 3. update evidence/ingest_Auto_DOCUMENT.csv
  docs_data = [
    DocData(
      dateOfIssue=file_creation_date,
      versionNumber=daikon_basic_data.version,
      description='Daikon Manual',
      identifier=f'DOCUMENT_DAIKON_{daikon_basic_data.doc_id()}',
      title=f'Daikon Manual {daikon_basic_data.version}',
      approvalAuthority_identifier='ORG_UW',
      issuingOrganization_identifier='ORG_UW',
      content_identifier=f'FILE_DAIKON_{daikon_basic_data.doc_id()}'),]

  ingest_doc_file = os.path.join(evidence_directory, "ingest_Auto_DOCUMENT.csv")
  with open(ingest_doc_file, "a") as f:
    try:
      w = DataclassWriter(f, docs_data, DocData)
      w.write()
    except Exception:
      common.log(args, 'csve', f'Failed to write {ingest_doc_file}')
      return
  
  # 4. _update_ evidence/ingest_Auto_FILE.csv
  tool_file_data = []
  supporting_files = daikon_basic_data['Evidence']['DAIKON_INVS_AND_METRICS']['SUPPORT_FILES']
  for supporting_file in supporting_files:
    file_parts = os.path.splitext(supporting_file)
    filename = os.path.basename(file_parts[0])
    filename_snake = camel_to_snake(filename)
    file_ext = file_parts[1].replace('.', '').upper()
    file_identifier = f"FILE_{filename_snake}".upper()
    file_data = FileData(
      filename=os.path.basename(supporting_file),
      description='Supporting file',
      generatedAtTime=file_creation_date,
      identifier=file_identifier,
      title=filename_snake.replace('_', ' '),
      fileFormat_identifier=f'FORMAT_{file_ext}',
      wasGeneratedBy_identifier=daikon_basic_data.identifier())
    tool_file_data += [file_data]
    
  manual_url = daikon_basic_data['Evidence']["DAIKON_TOOL_QUALIFICATION"]["USERGUIDE"]
  tool_file_data += [
    FileData(
      filename=manual_url,
      description=f'Daikon Manual {daikon_basic_data.version}',
      generatedAtTime=file_creation_date,
      identifier=f'FILE_DAIKON_{daikon_basic_data.doc_id()}',
      title=f'Daikon Manual {daikon_basic_data.version}',
      fileFormat_identifier='FORMAT_HTML',
      wasGeneratedBy_identifier='Michael_Ernst')]
    
  ingest_file = os.path.join(evidence_directory, "ingest_Auto_FILE.csv")
  with open(ingest_file, "a") as f:
    try:
      w = DataclassWriter(f, tool_file_data, FileData)
      w.write()
    except Exception:
      common.log(args, 'csve', f'Failed to write {ingest_file}')
      return

  # 5. create evidence/ingest_Auto_DaikonInvariantDetection.csv  
  daikon_detect_data = ToolOutputData(
    description=f"{daikon_basic_data.title()} detection",
    identifier=f"{daikon_basic_data.identifier()}_DETECT",
    title=f"{daikon_basic_data.title()} invariant detection",
    testGenInfo_identifier=f'{daikon_basic_data.identifier()}_INVOKE_INFO',
    testGenInput_identifier=daikon_basic_data.identifier())
  
  ingest_invs_detect_file = os.path.join(evidence_directory, "ingest_Auto_DaikonInvariantDetection.csv")
  with open(ingest_invs_detect_file, "w") as f:
    try:
      w = DataclassWriter(f, [daikon_detect_data], ToolOutputData)
      w.write()
    except Exception:
      common.log(args, 'csve', f'Failed to write {ingest_invs_detect_file}')
      return

  # 6. create evidence/ingest_Auto_LikelyInvariantModel.csv
  ppt_count = daikon_basic_data['Evidence']['DAIKON_INVS_AND_METRICS']['PPT_COUNT']
  cls_count = daikon_basic_data['Evidence']['DAIKON_INVS_AND_METRICS']['CLASSES_COUNT']
  daikon_inv_output = DaikonInvsData(
    classesCount=cls_count,
    invariantCount=ppt_count,
    testsCount=0,
    description=f"{daikon_basic_data.title()} output data",
    identifier=f"{daikon_basic_data.identifier()}_OUT",
    title=f"{daikon_basic_data.title()} invariant detection")

  detected_invariants = get_invariants(daikon_basic_data.identifier(), out_dir)
  ingest_likely_invs_file = os.path.join(evidence_directory, "ingest_Auto_LikelyInvariantModel.csv")
  with open(ingest_likely_invs_file, "w") as f:
    try:
      w = DataclassWriter(f, detected_invariants, LikelyProgramInvariant)
      w.write()
    except Exception:
      common.log(args, 'csve', f'Failed to write {ingest_likely_invs_file}')
      return
  
  # 7. create evidence/ingest_Auto_DaikonInvariantOutput.csv
  daikon_inv_output_data = [replace(daikon_inv_output, likelyInvariants_identifier=inv_obj.identifier)
                            for inv_obj in detected_invariants]

  ingest_invs_output_file = os.path.join(evidence_directory, "ingest_Auto_DaikonInvariantOutput.csv")
  with open(ingest_invs_output_file, "w") as f:
    try:
      w = DataclassWriter(f, daikon_inv_output_data, DaikonInvsData)
      w.write()
    except Exception:
      common.log(args, 'csve', f'Failed to write {ingest_invs_output_file}')
      return
  
  common.log(args, 'csve', f'Finished writing Daikon evidence data to {evidence_directory}')


