import pathlib
import os

from tfc_PyFactory.InputParameters import InputParameters
file_path = str(pathlib.Path(__file__).parent.resolve()) + "/"

import sys
sys.path.append(file_path + "../../")

import tfc_PyFactory
from tfc_PyFactory import *

from .CheckBase import *

class TextFileDiffCheck(CheckBase):
    '''Checks that two test files match exactly.'''
    @staticmethod
    def getInputParameters() -> InputParameters:
        params = CheckBase.getInputParameters()

        params.addRequiredParam("gold_file", ParameterType.STRING,
                                "Path to the file who has the golden content.")
        params.addRequiredParam("check_file", ParameterType.STRING,
                                "Path to the file that needs to match the gold_file.")
        params.addOptionalParam("inverse", False, "If true the check will only pass if" +
                                " the files do NOT match.")

        return params


    def __init__(self, params: InputParameters) -> None:
        super().__init__(params)

        self.gold_file_ = params.getParam("gold_file").getStringValue()
        self.check_file_ = params.getParam("check_file").getStringValue()
        self.inverse_ = params.getParam("inverse").getBooleanValue()

    def executeCheck(self, config: dict, annotations: list[str]) -> bool:
        dir_ = config["work_directory"]

        # Open gold file
        gold_file_name = dir_ + "/" + self.gold_file_
        try:
            gold_file = open(gold_file_name, "r")
        except Exception as ex:
            message = f'Error opening file "{gold_file_name}".'
            annotations.append("Python FileIOError")
            self.failed_ = True
            self.fail_reason_ = message
            return False

        # Open check file
        check_file_name = dir_ + "/" + self.check_file_
        try:
            check_file = open(check_file_name, "r")
        except Exception as ex:
            message = f'Error opening file "{check_file_name}".'
            annotations.append("Python FileIOError")
            self.failed_ = True
            self.fail_reason_ = message
            return False

        gold_file_lines = gold_file.readlines()
        check_file_lines = check_file.readlines()

        for i in range(0, max(len(check_file_lines),len(gold_file_lines))):
            if i >= len(gold_file_lines) and not self.inverse_:
                message = f'Check file {check_file_name} line {i}:\n' + \
                          f'{check_file_lines[i]} ' + \
                          f'missing from gold file {gold_file_name}'
                self.failed_ = True
                self.fail_reason_ = message
                gold_file.close()
                check_file.close()
                return False
            gold_line = gold_file_lines[i].strip()
            if i >= len(check_file_lines) and not self.inverse_:
                message = f'Gold file {gold_file_name} line {i}:\n' + \
                          f'{gold_line} ' + \
                          f'missing from check file {check_file_name}'
                self.failed_ = True
                self.fail_reason_ = message
                gold_file.close()
                check_file.close()
                return False

            if check_file_lines[i].strip() != gold_line and not self.inverse_:
                message = f'Check file {check_file_name} line {i}:\n' + \
                          f'{check_file_lines[i]} ' + \
                          f'does not match gold file:\n' + \
                          f'{gold_line}'
                self.failed_ = True
                self.fail_reason_ = message
                gold_file.close()
                check_file.close()
                return False


        return True


PyFactory.register(TextFileDiffCheck, "TextFileDiffCheck")
