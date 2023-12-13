from .TFCObject import TFCObject
from .InputParameters import Parameter, InputParameters

import json
import yaml

class PyFactory:
    registered_objects_: dict[str, TFCObject] = {}

    @staticmethod
    def register(obj, type_name):
        PyFactory.registered_objects_[type_name] = obj

    @staticmethod
    def makeObject(name: str, params: Parameter):
        type_name = params.getParam("type").getStringValue()

        params.addParameter("name", name)

        # find the object
        if not type_name in PyFactory.registered_objects_:
            raise RuntimeError("Object \"" + type_name +
                               "\" is not a registered object")

        obj = PyFactory.registered_objects_[type_name]
        valid_params = obj.getInputParameters()

        if not isinstance(valid_params, InputParameters):
            raise RuntimeError("The getInputParameters method of object \"" + type_name +
                               "\" does not seem to return a type 'InputParameters'")

        try:
            valid_params.assignParameters(params)
        except Exception as ex:
            raise RuntimeError("\033[31mERROR: Assigning parameters for object \"" +
                  name + "\"\n" + ex.__str__() + "\033[0m")

        return obj(valid_params)

    @staticmethod
    def readYAML(file_path: str) -> list:
        yaml_file = open(file_path)
        yaml_dict = yaml.safe_load(yaml_file)

        obj_dict = {}
        for obj_name in yaml_dict:
            if obj_name in obj_dict:
                print(f"\033[31mERROR: Duplicate object name \"{obj_name}\"\033[0m")
                raise SyntaxError()

            if not isinstance(obj_name, str):
                raise SyntaxError(str(obj_name) + " should be a string")
            obj_params = yaml_dict[obj_name]
            if not isinstance(obj_params, dict):
                raise SyntaxError("Value of object \"" + str(obj_name) + "\" should be a dict")
            new_obj = PyFactory.makeObject(obj_name, Parameter("", obj_params))

            obj_dict[obj_name] = new_obj


