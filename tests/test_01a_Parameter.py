import sys
sys.path.append("..")
import InputParameters
from InputParameters import Parameter

import json
import yaml

p1 = Parameter("dt", 0.01)
p2 = Parameter("dt", 0.0)

print(p1.getBooleanValue())
print(p2.getBooleanValue())

json_file = open("input_file.json")

p3 = Parameter("p3", json.load(json_file))

print(p3)

yaml_file = open("input_file.yaml")

p4 = Parameter("p4", yaml.safe_load(yaml_file))

print()
print(p4)

print()
print(p4.getParam("formed"))

p4_x = p4.getParam("x_values")
print(p4_x.getParam(1))
p4.getParam("x_values").setValue(99.99)
print(p4_x)