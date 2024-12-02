import pathlib

from tfc_PyFactory.InputParameters import InputParameters
file_path = str(pathlib.Path(__file__).parent.resolve()) + "/"

import sys
sys.path.append(file_path + "../../")

import tfc_PyFactory
from tfc_PyFactory import *

from .CheckBase import *

class ExitCodeCheck(CheckBase):
    '''Compares the test's exit code against a desired value.'''
    @staticmethod
    def getInputParameters() -> InputParameters:
        params = CheckBase.getInputParameters()

        params.addOptionalParam("gold_value", int(0),
                                "The exit code required.")

        return params


    def __init__(self, params: InputParameters) -> None:
        super().__init__(params)

        self.gold_value_ = params.getParam("gold_value").getIntegerValue()


    def executeCheck(self, config: dict, annotations: list[str]) -> bool:
        if config["error_code"] != self.gold_value_:
            self.failed_ = True
            self.fail_reason_ = \
            f'Error code, {config["error_code"]}, does not match' + \
            f' required value, {self.gold_value_}.'
            return False

        return True


PyFactory.register(ExitCodeCheck, "ExitCodeCheck")
