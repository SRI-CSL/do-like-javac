#!/usr/bin/env python

import os, tempfile, urllib.request, urllib.parse, urllib.error, zipfile, shutil, json, sys, subprocess, copy
from contextlib import contextmanager

WORKING_DIR = os.path.dirname(os.path.realpath(__file__))
CORPUS_DIR = os.path.join(WORKING_DIR, "corpus")
LOG_FILE = None

def load_corpus_info():
  with open(os.path.join(WORKING_DIR, 'corpus.json')) as f:
    info = json.loads(f.read())
    global_properties = info.get('global', {})
    projects = info['projects']

    for project_name in list(projects.keys()):
      base = copy.deepcopy(global_properties)
      base['name'] = project_name
      base.update(projects[project_name])
      projects[project_name] = base

    return info

CORPUS_INFO = load_corpus_info()

def get_corpus_set(setname):
  global CORPUS_INFO
  corpus = CORPUS_INFO

  if setname == "all":
    return list(corpus['projects'].keys())
  else:
    return corpus['sets'][setname]

def write_log(line):
  global LOG_FILE
  if LOG_FILE:
    LOG_FILE.write(line)
    LOG_FILE.flush()

def run_cmd(cmd):
  stats = {'output': ''}

  write_log("Running command '{}'\n".format(' '.join(cmd)))

  process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
  stats['output'] = process.stdout.decode('utf-8')
  write_log(stats['output'])

  if process.returncode != 0:
    print("Error running command '{}', check corpus.log for details.".format(' '.join(cmd)))

  write_log("\n\n")

  return stats

def run_git(subcommand, args=None, opts=None):
  cmd = ['git', subcommand]
  if opts:
    cmd.extend(opts)
  if args:
    cmd.extend(args)

  return run_cmd(cmd)

@contextmanager
def cd(newdir):
  prevdir = os.getcwd()
  os.chdir(os.path.expanduser(newdir))
  try:
    yield
  finally:
    os.chdir(prevdir)

def git_update(project):
  if project['git-url'] not in run_cmd(['git', 'remote', '-v'])['output']:
    print("git_url for {} has changed. Please delete the directory to redownload.".format(project['name']))
    return
  if project['git-ref'] not in run_cmd(['git', 'rev-parse', 'HEAD'])['output']:
    print("Checking out git ref %s." % project['git-ref'])
    run_git('fetch')
    run_git('reset', ['--hard'])
    run_git('checkout', [project['git-ref']])

def download_project(project):
  if not os.path.isdir(project['name']):
    if 'git-url' in project:
      opts = None
      if 'git-opt' in project:
        opts = project['git-opt'].split()
      print("Downloading %s" % project['name'])
      run_git('clone', [project['git-url'], project['name']], opts=opts)
  else:
    print("Already downloaded %s." % (project['name']))

def update_project(project):
  with cd(project['name']):
    if 'git-url' in project:
      git_update(project)

def fetch_project(project_name):
  with cd(CORPUS_DIR):
    project = CORPUS_INFO['projects'][project_name]
    download_project(project)

    if os.path.isdir(project['name']):
      update_project(project)
    else:
      print("{} not available.".format(project['name']))


def fetch_corpus(projects):
  global LOG_FILE
  LOG_FILE = open(os.path.join(WORKING_DIR, 'corpus.log'), 'w')

  with cd(CORPUS_DIR):
    for project_name in projects:
      fetch_project(project_name)

  LOG_FILE.close()
  LOG_FILE = None

if __name__ == "__main__":
  if len(sys.argv) > 1:
    if len(sys.argv) == 2 and get_corpus_set(sys.argv[1]):
      setname = sys.argv[1]
      print(("Fetching corpus subset labeled {}".format(setname)))
      to_fetch = get_corpus_set(setname)
    else:
      to_fetch = sys.argv[1:]
      print(("Fetching {}".format(', '.join(to_fetch))))
  else:
    print("Fetching entire corpus")
    to_fetch = get_corpus_set("all")

  fetch_corpus(to_fetch)
