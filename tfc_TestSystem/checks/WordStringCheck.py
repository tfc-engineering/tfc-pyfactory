import pathlib

from tfc_PyFactory.InputParameters import InputParameters
file_path = str(pathlib.Path(__file__).parent.resolve()) + "/"

import sys
sys.path.append(file_path + "../../")

import tfc_PyFactory
from tfc_PyFactory import *

from .CheckBase import *

class WordStringCheck(CheckBase):
    '''Performs a check on a specific word of type str.'''
    @staticmethod
    def getInputParameters() -> InputParameters:
        params = CheckBase.getInputParameters()

        params.addRequiredParam("line_key", ParameterType.STRING,
                                "The string to find in order to identify the "
                                "line of interest.")
        params.addRequiredParam("word_number", ParameterType.INTEGER,
                                "Which word (zero-based id) to be compared to "
                                "the gold value.")
        params.addRequiredParam("gold_value", ParameterType.STRING,
                                "The string required to match.")
        params.addOptionalParam("reverse_line_traverse", False,
                                "If true will reverse the traversal of file lines.")
        params.addOptionalParam("word_delimiters", " ",
                                "Characters that must be used as delimeters for "
                                "separating words.")

        return params


    def __init__(self, params: InputParameters) -> None:
        super().__init__(params)

        self.line_key_ = params.getParam("line_key").getStringValue()
        self.word_number_ = params.getParam("word_number").getIntegerValue()
        self.gold_value_ = params.getParam("gold_value").getStringValue()

        self.reverse_line_traverse_ = \
            params.getParam("reverse_line_traverse").getBooleanValue()
        self.word_delimiters_ = \
            params.getParam("word_delimiters").getStringValue()

        self._cast_type = str


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

        if relevant_line == None:
            message = f'Could not find line containing "{self.line_key_}".'
            self.failed_ = True
            self.fail_reason_ = message
            return False
        relevant_line = relevant_line.rstrip()

        relevant_word = None
        words = relevant_line.split(self.word_delimiters_)

        if (len(words) - 1) < self.word_number_:
            message = f'Line {relevant_line_num} does not have enough words ' + \
              f'({len(words)}) given that the gold value is to be compared ' + \
              f'to word {self.word_number_}.'
            self.failed_ = True
            self.fail_reason_ = message
            return False

        relevant_value = None
        try:
            relevant_word = words[self.word_number_]
            relevant_value = self._cast_type(relevant_word)
        except Exception as ex:
            message = f'Line {relevant_line_num}, failed to convert word ' + \
                f'{self.word_number_} ("{relevant_word}") to type ' + \
                f'{self._cast_type}.'
            annotations.append("Python error")
            self.failed_ = True
            self.fail_reason_ = message
            return False

        if relevant_value != self.gold_value_:
            message = f'Line {relevant_line_num}, word ' + \
                f'{self.word_number_} ("{relevant_word}"), failed gold value ' + \
                f'evalutaion: "{relevant_word}" != "{self.gold_value_}".'
            print(message)
            self.failed_ = True
            self.fail_reason_ = message
            out_file.close()
            return False
        else:
            out_file.close()
            return True


PyFactory.register(WordStringCheck, "WordStringCheck")
