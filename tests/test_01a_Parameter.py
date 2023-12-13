import pathlib
file_path = str(pathlib.Path(__file__).parent.resolve()) + "/"

import sys
sys.path.append(file_path + "../")

from tfc_PyFactory import *

import json
import yaml

p1 = Parameter("dt", 0.01)
p2 = Parameter("dt", 0.0)

print(p1.getBooleanValue())
print(p2.getBooleanValue())

json_file = open(file_path + "test_01a.json")

p3 = Parameter("p3", json.load(json_file))

print(p3)

yaml_file = open(file_path + "test_01a.yaml")

p4 = Parameter("p4", yaml.safe_load(yaml_file))

print()
print(p4)

print()
print(p4.getParam("formed"))

p4_x = p4.getParam("x_values")
print(p4_x.getParam(1))
p4.getParam("x_values").setValue(99.99)
print(p4_x)
