import pathlib
file_path = str(pathlib.Path(__file__).parent.resolve()) + "/"

import sys
sys.path.append(file_path + "../")

from tfc_PyFactory import *


class TestObject(TFCObject):
    @staticmethod
    def getInputParameters() -> InputParameters:
        params = TFCObject.getInputParameters()
        params.addRequiredParam(
            "option", ParameterType.INTEGER, "A simple test option")
        params.addOptionalParam("option2", 2, "Another simple option")

        return params

    def __init__(self, params: InputParameters) -> None:
        super().__init__(params)

        print("TestObject created")
        print(f"option = {params.getParam('option').getValue()}")
        print(f"option2 = {params.getParam('option2').getValue()}")

PyFactory.register(TestObject, "TestObject")

PyFactory.readYAML(file_path + "test_02b.yaml")
