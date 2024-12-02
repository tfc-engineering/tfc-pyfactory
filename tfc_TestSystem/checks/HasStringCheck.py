import pathlib

from tfc_PyFactory.InputParameters import InputParameters
file_path = str(pathlib.Path(__file__).parent.resolve()) + "/"

import sys
sys.path.append(file_path + "../../")

import tfc_PyFactory
from tfc_PyFactory import *

from .CheckBase import *

class HasStringCheck(CheckBase):
    '''Checks for presence or abscence of a string in the output of a test.'''
    @staticmethod
    def getInputParameters() -> InputParameters:
        params = CheckBase.getInputParameters()

        params.addRequiredParam("line_key", ParameterType.STRING,
                                "The string to find in order to identify the "
                                "line of interest.")
        params.addOptionalParam("reverse_line_traverse", False,
                                "If true will reverse the traversal of file lines.")

        params.addOptionalParam("fail_if_present", False,
                                "Inverts the check. Fails if the line_key is indeed found.")

        return params


    def __init__(self, params: InputParameters) -> None:
        super().__init__(params)

        self.line_key_ = params.getParam("line_key").getStringValue()

        self.reverse_line_traverse_ = \
            params.getParam("reverse_line_traverse").getBooleanValue()

        self.fail_if_present_ = self.reverse_line_traverse_ = \
            params.getParam("fail_if_present").getBooleanValue()


    def executeCheck(self, config: dict, annotations: list[str]) -> bool:
        out_file_name = config["out_file_name"]
        try:
            out_file = open(out_file_name, "r")
        except Exception as ex:
            message = f'Error opening file "{out_file_name}".'
            annotations.append("Python FileIOError")
            self.failed_ = True
            self.fail_reason_ = message
            return False

        lines = out_file.readlines()
        relevant_line = None
        relevant_line_num = -1

        if not self.reverse_line_traverse_:
            line_num = 0
            for line in lines:
                line_num += 1
                if line.find(self.line_key_) >= 0:
                    relevant_line = line
                    relevant_line_num = line_num
                    break
        else:
            for line in reversed(lines):
                if line.find(self.line_key_) >= 0:
                    relevant_line = line
                    break

        if not self.fail_if_present_:
            if relevant_line == None:
                message = f'Could not find line containing "{self.line_key_}".'
                self.failed_ = True
                self.fail_reason_ = message
                return False
            else:
                return True
        else:
            if relevant_line == None:
                return True
            else:
                message = f'Found line containing "{self.line_key_}".'
                self.failed_ = True
                self.fail_reason_ = message
                return False



PyFactory.register(HasStringCheck, "HasStringCheck")
