import pathlib

from tfc_PyFactory.InputParameters import InputParameters
file_path = str(pathlib.Path(__file__).parent.resolve()) + "/"

import sys
sys.path.append(file_path + "../../")

import tfc_PyFactory
from tfc_PyFactory import *

class CheckBase(TFCObject):
    @staticmethod
    def getInputParameters() -> InputParameters:
        params = TFCObject.getInputParameters()

        return params


    def __init__(self, params: InputParameters) -> None:
        super().__init__(params)

        self.failed_: bool = False
        self.fail_reason_: str = "Unknown"


    # config = dict(
    #         test = self,
    #         test_system = test_system,
    #         error_code = error_code,
    #         out_file_name = out_file_name,
    #         out_directory = dir_+"/out"
    #     )
    def executeCheck(self, config: dict, annotations: list[str]) -> bool:
        """Executes a given check.
        The 'annotations' parameter is a list of annotations to provide
        on the Pass/Fail status line of the test. Use the annotations to
        indicate that the check failed to execute, not the reason for it's
        failure."""
        return True
