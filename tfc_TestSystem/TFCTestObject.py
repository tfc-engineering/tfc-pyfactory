"""Definition and registration of TFCTestObject"""
from __future__ import annotations
import sys
import pathlib
import math
import subprocess
import os
import time

from tfc_PyFactory.InputParameters import InputParameters
FILE_PATH = str(pathlib.Path(__file__).parent.resolve()) + "/"

sys.path.append(FILE_PATH + "../")

import tfc_PyFactory
from tfc_PyFactory import *

from checks import *


class TFCTestObject(TFCObject):
    """A Test object to organize tests"""
    @staticmethod
    def getInputParameters() -> InputParameters:
        params = TFCObject.getInputParameters()

        params.addRequiredParam("args", ParameterType.STRING,
                                "Arguments to pass to the test program.")
        params.addOptionalParam("disable_mpi", True,
                                "Flag to suppress running the application "
                                "via mpi.")
        params.addOptionalParam("num_procs", 1,
                                "The number of mpi processes used.")
        params.addOptionalParam("weight_class", "short",
                                "The weight class short/intermediate/long")
        params.addOptionalParam("outfileprefix", "",
                                'Will default to the test name + .out, '
                                'otherwise outfileprefix+.out.')
        params.addOptionalParam("skip", "",
                                "If non-empty, will skip with this message.")

        params.addRequiredParam("checks", ParameterType.ARRAY,
                                "An array of check-inputs.")
        params.addOptionalParam("dependencies", [""],
                                "A list of dependent test names before this test can run.")

        return params


    def __init__(self, params: InputParameters) -> None:
        super().__init__(params)

        self.args_ = params.getParam("args").getStringValue()
        self.disable_mpi_ = params.getParam("disable_mpi").getBooleanValue()
        self.num_procs_ = params.getParam("num_procs").getIntegerValue()
        self.weight_class_ = params.getParam("weight_class").getStringValue()
        self.outfileprefix_ = params.getParam("outfileprefix").getStringValue()
        self.skip_ = params.getParam("skip").getStringValue()
        self.dependencies_ = params.getParam("dependencies")

        self.checks_: list[CheckBase] = []
        self._process_ = None
        self._time_start_ = time.perf_counter()
        self._time_end_ = time.perf_counter()
        self._command_ = ""

        check_inputs = params.getParam("checks")
        for check_input in check_inputs:
            id = str(len(self.checks_))
            check = PyFactory.makeObject(id, check_input)
            self.checks_.append(check)

        print(f'Created test \"{self.name_}\" with {len(self.checks_)} checks')

        self.ran_: bool = False
        self.submitted_: bool = False
        self.passed_: bool = False


    def checkDependenciesMet(self, tests: list[TFCTestObject]) -> bool:
        """Determines, from the supplied tests-list, whether this
        test's dependendent tests have run.
        """
        for dependency in self.dependencies_:
            dep_name = dependency.getStringValue()
            for test in tests:
                test_name = test.name_
                last_dash = test_name.rfind("/")
                test_true_name = test_name if last_dash < 0 else test_name[last_dash:]

                if test_true_name == dep_name and not test.ran_:
                    return False
        return True

    def submit(self, test_system) -> None:
        """Submits the test to a process call"""
        self.submitted_ = True

        cmd = ""
        if not self.disable_mpi_:
            cmd += "mpiexec "
            cmd += "-np " + str(self.num_procs_) + " "
        cmd += test_system.executable_ + " "
        cmd += self.args_ + " "

        self._command_ = cmd

        dir_, filename_ = os.path.split(self.name_)

        self._time_start_ = time.perf_counter()

        if self.skip_ != "":
            return

        self._process_ = subprocess.Popen(cmd,
                                        cwd=dir_,
                                        shell=True,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        universal_newlines=True)


    def checkProgress(self, test_system) -> str:
        """Checks whether the process is running and returns 'Running' if it is.
        If it is not running anymore the checks will be executed."""

        if self.ran_:
            return "Done"

        error_code = 0
        out_file_name = ""
        dir_, testname_ = os.path.split(self.name_)
        annotations = []
        cntl_char_pad = 0

        if self.skip_ == "":
            if self._process_.poll() is not None:

                out, err = self._process_.communicate()
                error_code = self._process_.returncode

                self._time_end_ = time.perf_counter()

                if not os.path.isdir(dir_+"/out"):
                    os.mkdir(dir_+"/out")

                prefix = testname_ if self.outfileprefix_ == "" else self.outfileprefix_

                out_file_name = dir_ + f"/out/{prefix}.out"
                file = open(out_file_name, "w")
                file.write(self._command_ + "\n")
                file.write(out + "\n")
                file.write(err + "\n")
                file.close()
                self.ran_ = True
            else:
                return "Running"

            self.passed_ = True
            test_config = dict(
                test = self,
                test_system = test_system,
                error_code = error_code,
                out_file_name = out_file_name,
                out_directory = dir_+"/out"
            )

            for check in self.checks_:
                result = check.executeCheck(test_config, annotations)
                if not result:
                    self.passed_ = False
        else: # skipped
            self._time_end_ = time.perf_counter()
            self.passed_ = True
            self.ran_ = True
            annotations.append( f"skipped:{self.skip_}" )

        max_num_procs = test_system.max_num_procs_
        pcount_width = int(math.floor(math.log10(max_num_procs)))+1

        prefix = f"\033[33m[{self.num_procs_:{pcount_width}d}]\033[0m "
        cntl_char_pad += 5 + 4

        suffix = ""
        for annotation in annotations:
            suffix += "\033[36m[" + annotation + "]\033[0m"
            cntl_char_pad += 5 + 4
        suffix += "\033[32mPassed\033[0m" if self.passed_ else "\033[31mFailed\033[0m"
        cntl_char_pad += 5 + 4

        time_taken = self._time_end_ - self._time_start_

        width = test_system.print_width_ - len(prefix) - len(self.name_) \
              - len(suffix) + cntl_char_pad
        width = max(width, 0)

        suffix = '.' * width + suffix + f" {time_taken:.1g}s"

        message = prefix + self.name_ + suffix

        print(message)

        return "Done"


PyFactory.register(TFCTestObject, "TFCTestObject")
