import os
import re
import xml.etree.ElementTree as ET

from . import common


def generate_json_invariants(args, out_dir):
  filename = os.path.join(out_dir, 'invariants.xml')
  if not os.path.exists(filename):
    return

  try:
    tree = ET.parse(filename)
  except:
    common.log(args, 'jsoninv', f'Failed to parse {filename}')
    return

  invariants = tree.getroot()
  methods = {}

  for ppt in invariants:
    add_ppt(methods, ppt)

  js = {"invariants": list(methods.values())}

  return js
  
def add_ppt(methods, ppt):
  class_name, method_name, args, point = ppt_info(ppt)

  if point not in ['ENTER', 'EXIT']:
    return

  method = find_method(methods, class_name, method_name, args)

  for inv in ppt.iter('INVINFO'):
    add_inv(method, inv)

def ppt_info(ppt):
  name = ppt.find('PPTNAME').text

  signature, point = name.split(':::')
  if '(' not in signature:
    return signature, None, None, point

  match = re.match(r'(.*)\.([^\(.]+)\.?\((.*)\)', signature)
  class_name, method_name, args = match.groups()
  if args:
    args = args.split(', ')
  else:
    args = []

  return class_name, method_name, args, point

def find_method(methods, class_name, method_name, args):
  descriptor = f"{class_name}.{method_name}({args})"
  if descriptor not in methods:
    methods[descriptor] = {"cls": class_name,
                           "method": method_name,
                           "params": args,
                           "preconds": [],
                           "postconds": []}

  return methods[descriptor]

def add_inv(method, inv):
  i = None
  point = inv.find('PARENT').text
  inv_txt = inv.find('INV').text

  pattern = r'(.*) ([=!<>]+|one of) (.*)'
  match = re.match(pattern, inv_txt)
  if match:
    left, op, right = match.groups()
    i = {"left": left, "right": right, "op": op}
  else:
    i = {"inv": inv_txt}

  if point == "ENTER":
    method['preconds'].append(i)
  else:
    method['postconds'].append(i)
