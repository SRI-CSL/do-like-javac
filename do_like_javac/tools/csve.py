import argparse
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
  '--override-csv',
  action='store_true',
  dest='override_csv',
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
    return f'{self.qual_title}-{self.version}'
  
  def title(self) -> str:
    return f'{self.qual_title} version {self.version}'
  
  def user_guide_id(self) -> str:
    return f'DOCUMENT_{self.qual_title.upper()} version {self.doc_id()}'
  

@dataclass(frozen=True)
class ToolData:
  toolSummaryDescription: str
  toolVersion: str
  description: str
  identifier: str
  title: str
  userGuide_identifier: str

@dataclass(frozen=True)
@dateformat("%Y-%m-%dT%H:%M:%S.%f%z")
class ToolInvokeData:
  description: str
  generatedAtTime: datetime
  identifier: str
  invalidatedAtTime: datetime
  title: str
  toolParamaters: str
  definedIn_identifier: str
  dataInsertedBy_identifier: str

@dataclass(frozen=True)
@dateformat("%Y-%m-%dT%H:%M:%S.%f%z")
class FileData:
  filename: str
  description: str
  generatedAtTime: datetime
  identifier: str
  invalidatedAtTime: datetime
  title: str
  createBy_identifier: str
  definedIn_identifier: str
  fileFormat_identifier: str
  fileHash_identifier: str
  satisfies_identifier: str
  dataInsertedBy_identifier: str
  wasAttributedTo_identifier: str
  wasDerivedFrom_identifier: str
  wasGeneratedBy_identifier: str
  wasImpactedBy_identifier: str
  wasRevisionOf_identifier: str

@dataclass(frozen=True)
@dateformat("%Y-%m-%dT%H:%M:%S.%f%z")
class ToolMetricData:
  numberOfErrorRevealingTestCases: int
  numberOfReducedViolationInducingTestCases: int
  numberOfRegressionTestCases: int
  numberOfViolationInducingTestCases: int
  # Note: explicitly defined given that a method named `totalNumberOfTestCases` 
  # which returns numberOfErrorRevealingTestCases + numberOfRegressionTestCases 
  # is not written as a column in a csv file.
  totalNumberOfTestCases: int
  description: str
  generatedAtTime: datetime
  identifier: str
  title: str
  jUnitTestFile_identifier: str
  producedBy_identifier: str
  verifies_identifier: str
  definedIn_identifier: str
  dataInsertedBy_identifier: str
  wasAttributedTo_identifier: str
  wasDerivedFrom_identifier: str
  wasGeneratedBy_identifier: str
  wasImpactedBy_identifier: str
  asRevisionOf_identifier: str

@dataclass(frozen=True)
@dateformat("%Y-%m-%dT%H:%M:%S.%f%z")
class JUnitGenData:
  description: str
  endedAtTime: datetime
  identifier: str
  startedAtTime: datetime
  title: str
  definedIn_identifier: str
  dataInsertedBy_identifier: str
  used_identifier: str
  wasAssociatedWith_identifier: str
  wasInformedBy_identifier: str
  developedBy_identifier: str
  toolInvocation_identifier: str

@dataclass(frozen=True)
@dateformat("%Y-%m-%dT%H:%M:%S.%f%z")
class DocData:
  dateOfIssue: datetime
  versionNumber: str
  description: str
  generatedAtTime: datetime 
  identifier: str
  invalidatedAtTime: datetime
  title: str
  approvalAuthority_identifier: str
  issuingOrganization_identifier: str
  references_identifier: str
  status_identifier: str
  definedIn_identifier: str
  content_identifier: str
  dataInsertedBy_identifier: str
  wasAttributedTo_identifier: str
  wasDerivedFrom_identifier: str
  wasGeneratedBy_identifier: str
  wasImpactedBy_identifier: str
  wasRevisionOf_identifier: str

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


def evidence_print_csv(args, java_command, out_dir):
  test_class_directory = get_test_class_directory('test-classes', out_dir)
  if not os.path.exists(test_class_directory):
    common.log(args, 'csve', f'Failed to locate {test_class_directory}')
    return
  
  randoop_evidence_json = os.path.join(test_class_directory, 'randoop-evidence.json')
  daikon_evidence_json = os.path.join(test_class_directory, 'daikon-evidence.json')
  if not os.path.exists(randoop_evidence_json) or not os.path.exists(daikon_evidence_json):
    common.log(args, 'csve', f'Failed to read {randoop_evidence_json} or {daikon_evidence_json}')
    return

  # from *_evidence_json to *_evidence_csv
  randoop_print_csv(args, randoop_evidence_json, out_dir)
  daikon_print_csv(args, randoop_evidence_json, out_dir)
  
  common.run_cmd([], args, 'csve')

def camel_to_snake(name):
  name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
  return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name)

def get_basic_randoop_info(randoop_data: dict) -> BasicData:
  randoop_tool = randoop_data['Evidence']["RANDOOP_TOOL_QUALIFICATION"]["TITLE"]
  randoop_version = randoop_data['Evidence']["RANDOOP_TOOL_QUALIFICATION"]["RANDOOP_VERSION"]
  randoop_summary = randoop_data['Evidence']["RANDOOP_TOOL_QUALIFICATION"]["SUMMARY"]
  randoop_desc = 'Randoop is a unit test generator for Java, in JUnit format.'
  
  return BasicData(
    qual_title=randoop_tool,
    version=randoop_version,
    summary=randoop_summary,
    description=randoop_desc)

def randoop_print_csv(args, randoop_evidence_json, out_dir):
  try:
    rej = open(randoop_evidence_json, 'r')
  except OSError:
    common.log(args, 'csve', f'Failed to read {randoop_evidence_json}')
    return

  randoop_data = json.loads(rej.read())

  # collect tool data
  randoop_basic_data = get_basic_randoop_info(randoop_data)

  # TODO(has) is this the right place of this code?
  evidence_directory = os.path.join(out_dir, "evidence")
  if not os.path.exists(evidence_directory):
    os.mkdir(evidence_directory)
  else:
    # rotate existing evidence directory
    rotate_and_make_dir(evidence_directory)
  
  # data to become
  tool_data = ToolData(
    toolSummaryDescription=randoop_basic_data.summary,
    toolVersion=randoop_basic_data.version,
    description=randoop_basic_data.description,
    identifier=randoop_basic_data.identifier(),
    title=randoop_basic_data.title(),
    userGuide_identifier=randoop_basic_data.user_guide_id())

  # 1. create evidence/ingest_Auto_TOOL.csv
  ingest_tool_file = os.path.join(evidence_directory, "ingest_Auto_TOOL.csv")
  with open(ingest_tool_file, "w") as f:
    try:
      w = DataclassWriter(f, [tool_data], ToolData)
      w.write()
    except Exception:
      common.log(args, 'csve', f'Failed to write {ingest_tool_file}')
      return

  # collect tool invocation data
  tool_invoke_data = []
  randoop_params = randoop_data['Evidence']['RANDOOP_JUNIT_TEST_GENERATION']['PARAMETERS']
  for each_param_dict in randoop_params:
    tool_name = next(iter(each_param_dict))
    tool_description = 'Build monitor for Java Projects' if tool_name == 'dljc' else randoop_basic_data.description
    tool_identifier = tool_name if tool_name == 'dljc' else randoop_basic_data.identifier()
    tool_title = 'do-like-javac (dljc)' if tool_name == 'dljc' else randoop_basic_data.title()
    tool_params = each_param_dict[tool_name]
    tool_invoke = ToolInvokeData(
      description=tool_description,
      generatedAtTime=date.today(),
      identifier=tool_identifier,
      title=tool_title,
      toolParamaters=tool_params,
      dataInsertedBy_identifier='dljc')
    tool_invoke_data += [tool_invoke]

  # 2. create evidence/ingest_Auto_TOOL_INVOCATION_INSTANCE.csv
  ingest_tool_invoke_file = os.path.join(evidence_directory, "ingest_Auto_TOOL_INVOCATION_INSTANCE.csv")
  with open(ingest_tool_invoke_file, "w") as f:
    try:
      w = DataclassWriter(f, tool_invoke_data, ToolInvokeData)
      w.write()
    except Exception:
      common.log(args, 'csve', f'Failed to write {ingest_tool_invoke_file}')
      return

  # collect tool metrics data
  numberOfErrorRevealingTestCases = randoop_data['Evidence']['RANDOOP_TESTS_AND_METRICS']['ERROR_REVEALING_TEST_COUNT']
  numberOfRegressionTestCases = randoop_data['Evidence']['RANDOOP_TESTS_AND_METRICS']['REGRESSION_TEST_COUNT']
  tool_metric_data = ToolMetricData(
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
  tests_creation_date = randoop_data['Evidence']["RANDOOP_TOOL_QUALIFICATION"]["DATE"]
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
      identifier='FILE_RANDOOP_' + '_'.join(randoop_basic_data.version.split('.')),
      title=f'Randoop Manual {randoop_basic_data.version}',
      fileFormat_identifier='FORMAT_HTML')] # Randoop Manual
  tool_file_data += [
    FileData(
      filename='https://github.com/SRI-CSL/do-like-javac/blob/master/README.md',
      description='do-like-javac Manual 0.1',
      generatedAtTime=tests_creation_date,
      identifier='FILE_DLJC_0_1',
      title='do-like-javac Manual 0.1',
      fileFormat_identifier='FORMAT_MD')]

  # 3. create evidence/ingest_Auto_FILE.csv
  ingest_file = os.path.join(evidence_directory, "ingest_Auto_FILE.csv")
  with open(ingest_file, "w") as f:
    try:
      w = DataclassWriter(f, tool_file_data, FileData)
      w.write()
    except Exception:
      common.log(args, 'csve', f'Failed to write {ingest_file}')
      return

  # 4. create evidence/ingest_Auto_RANDOOP_TESTS_AND_METRICS.csv
  ingest_metrics_file = os.path.join(evidence_directory, "ingest_Auto_RANDOOP_TESTS_AND_METRICS.csv")
  with open(ingest_metrics_file, "w") as f:
    try:
      w = DataclassWriter(f, tool_metrics_data, ToolMetricData)
      w.write()
    except Exception:
      common.log(args, 'csve', f'Failed to write {ingest_metrics_file}')
      return

  # 5. create evidence/ingest_Auto_RANDOOP_JUNIT_TEST_GENERATION.csv
  junit_gen_data = JUnitGenData(
    description=f"{randoop_basic_data.title()} metrics",
    identifier=f"{randoop_basic_data.identifier()}_METRICS",
    title=f"{randoop_basic_data.title()} metrics data",
    wasGeneratedBy_identifier=randoop_basic_data.identifier())
  ingest_randoop_junit_file = os.path.join(evidence_directory, "ingest_Auto_RANDOOP_TESTS_AND_METRICS.csv")
  with open(ingest_randoop_junit_file, "w") as f:
    try:
      w = DataclassWriter(f, [junit_gen_data], JUnitGenData)
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
      identifier='DOCUMENT_RANDOOP_' + '_'.join(randoop_basic_data.version.split('.')),
      title=f'Randoop Manual {randoop_basic_data.version}',
      approvalAuthority_identifier='ORG_UW',
      issuingOrganization_identifier='ORG_UW',
      content_identifier='FILE_RANDOOP_' + '_'.join(randoop_basic_data.version.split('.'))),
    DocData(
      dateOfIssue=date.today(), 
      versionNumber='0.1',
      description='do-like-javac Manual',
      identifier='DOCUMENT_DLJC_0_1',
      title='do-like-javac Manual 0.1',
      approvalAuthority_identifier='ORG_SRI',
      issuingOrganization_identifier='ORG_SRI',
      content_identifier='FILE_DLJC_0_1')]
  with open(ingest_doc_file, "w") as f:
    try:
      w = DataclassWriter(f, docs_data, DocData)
      w.write()
    except Exception:
      common.log(args, 'csve', f'Failed to write {ingest_doc_file}')

def daikon_print_csv(args, daikon_evidence_json, out_dir):
  try:
    rej = open(daikon_evidence_json, 'r')
  except OSError:
    common.log(args, 'csve', f'Failed to read {daikon_evidence_json}')
    return
  pass
