from .InputParameters import *

class TFCObject:
    @staticmethod
    def getInputParameters() -> InputParameters:
        params = InputParameters()
        params.addRequiredParam(
            "name", ParameterType.STRING, "The name of the object")
        params.addRequiredParam(
            "type", ParameterType.STRING, "The type of the object")

        return params

    def __init__(self, params: InputParameters) -> None:
        self.name_ = params.getParam("name").getStringValue()
        self.type_ = params.getParam("type")
