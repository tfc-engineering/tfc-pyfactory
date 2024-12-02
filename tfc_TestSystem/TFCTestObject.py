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

TEST_SYSTEM_PATH = f'{FILE_PATH}/../../'
PROJECT_ROOT_PATH = f'{TEST_SYSTEM_PATH}/../'

import tfc_PyFactory
from tfc_PyFactory import *

from checks import *


class TFCTestObject(TFCObject):
    """A Test object to organize tests. This object will load up a test with all
    the necessary bells-and-whistles. When executed by the test system, the test
    will execute the optional prerun script, after which a process will be
    submitted according to the executable and arguments specified. The test
    system will then continuously ping the test to ascertain it's completion
    status, which it does by calling it's checkProgress method. In this method
    (if the test has completed) the test will execute its checks, run the
    optional postrun script and mark itself completed.

    The working directory of the test is by default the directory in which it's
    configuration file lives. A relative offset may be added with the
    relative_offset_workdir parameter.
    """
    @staticmethod
    def getInputParameters() -> InputParameters:
        params = TFCObject.getInputParameters()

        params.addRequiredParam("args", ParameterType.STRING,
                                "Arguments to pass to the test program.")
        params.addRequiredParam("checks", ParameterType.ARRAY,
                                "An array of check-inputs.")
        params.addRequiredParam("project_root", ParameterType.STRING,
                                "The path to the project root directory")
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
        params.addOptionalParam("dependencies", [""],
                                "A list of dependent test names before this test can run.")
        params.addOptionalParam("prerun_script", "",
                                "A shell script to run before the test is executed.")
        params.addOptionalParam("postrun_script", "",
                                "A shell script to run after the test is executed.")
        params.addOptionalParam("relative_offset_workdir", "",
                                "A relative working directory to be added to the "
                                "default working directory.")
        params.addOptionalParam("debug", False,
                                "Flag for debug printout. Will echo the output file to"
                                "the screen for failed tests")
        params.addOptionalParam("executable", "",
                                "Executable to use instead of system wide default.")
        params.addOptionalParam("copy_test", ["",""],
                                "A way to copy a given test and run it with a slight change"
                                "Input is a three item list specifying the name extension for the"
                                "new copied test, the path to the script to create the copied file,"
                                "and the file location of the input file to be copied.")

        return params


    def __init__(self, params: InputParameters) -> None:
        super().__init__(params)

        self.args_ = params.getParam("args").getStringValue()
        self.project_root_ = params.getParam("project_root").getStringValue()
        self.disable_mpi_ = params.getParam("disable_mpi").getBooleanValue()
        self.num_procs_ = params.getParam("num_procs").getIntegerValue()
        self.weight_class_ = params.getParam("weight_class").getStringValue()
        self.outfileprefix_ = params.getParam("outfileprefix").getStringValue()
        self.skip_ = params.getParam("skip").getStringValue()
        self.dependencies_ = params.getParam("dependencies")
        self.prerun_script_ = params.getParam("prerun_script").getStringValue()
        self.postrun_script_ = params.getParam("postrun_script").getStringValue()
        self.relative_offset_workdir_ = \
          params.getParam("relative_offset_workdir").getStringValue()
        self.debug_ = params.getParam("debug").getBooleanValue()
        self.executable_ = params.getParam("executable").getStringValue()
        self.copy_test_ = params.getParam("copy_test")

        self.test_system_reference_ = None

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

        pretty_name = os.path.relpath(self.name_, PROJECT_ROOT_PATH)

        print(f'Created test-job \"{pretty_name}\" with {len(self.checks_)} checks')

        self.ran_: bool = False
        self.submitted_: bool = False
        self.passed_: bool = False


    def setTestSystemReference(self, ref):
        self.test_system_reference_ = ref

        self.relative_offset_workdir_ = \
          self.keywordReplace(self.relative_offset_workdir_)

    def keywordReplace(self, input) -> str:
        dir_, test_name = os.path.split(self.name_)
        output = input.replace("$TEST_NAME", test_name)
        output = output.replace("$PROJECT_ROOT", self.project_root_)

        env_vars = self.test_system_reference_.env_vars_

        for env_var_name in env_vars:
            if env_var_name in os.environ:
                env_var_value = os.environ[env_var_name]
                if env_var_value != None:
                    output = output.replace(f"${env_var_name}", str(env_var_value))

        return output

    def checkDependenciesMet(self, tests: list[TFCTestObject]) -> bool:
        """Determines, from the supplied tests-list, whether this
        test's dependendent tests have run.
        """
        for dependency in self.dependencies_:
            dep_name = dependency.getStringValue()
            for test in tests:
                test_name = test.name_
                last_dash = test_name.rfind("/")
                test_true_name = test_name if last_dash < 0 else test_name[last_dash+1:]

                if test_true_name == dep_name and not test.ran_:
                    return False
        return True

    def submit(self, test_system) -> None:
        """Submits the test to a process call"""
        self.submitted_ = True

        dir_, filename_ = os.path.split(self.name_)

        if not self.prerun_script_ == "":
            script = self.prerun_script_
            script = self.keywordReplace(script)
            preprocess = subprocess.Popen(script,
                                        cwd=dir_,
                                        shell=True,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        universal_newlines=True)

            out, err = preprocess.communicate()
            error_code = preprocess.returncode

            if error_code != 0:
                print('\033[31mERROR: Prerun script for test ' +
                 f'{self.name_}:\n{script}\n failed with:\n' +
                 f'{err}\n' +
                 f'Output:\n{out}' +
                 '\033[0m')

        cmd = ""
        if not self.disable_mpi_:
            cmd += "mpiexec "
            cmd += "-np " + str(self.num_procs_) + " "
        if self.executable_ == "":
            cmd += test_system.executable_ + " "
        else:
            cmd += self.executable_ + " "
        cmd += test_system.default_args_ + " "
        cmd += self.args_ + " "

        cmd = self.keywordReplace(cmd)

        self._command_ = cmd

        self._time_start_ = time.perf_counter()

        if self.skip_ != "":
            return

        # Make the output directory
        if not os.path.isdir(dir_+"/out"):
                    os.mkdir(dir_+"/out")

        self._process_ = subprocess.Popen(cmd,
                                        cwd=dir_ + "/" +
                                            self.relative_offset_workdir_,
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

                prefix = testname_ if self.outfileprefix_ == "" else self.outfileprefix_

                out_file_name = dir_ + f"/out/{prefix}.cout"
                file = open(out_file_name, "w")
                file.write(self._command_ + "\n")
                file.write(out + "\n")
                file.write(err + "\n")
                file.close()
                # self.ran_ = True
            else:
                return "Running"

            self.passed_ = True
            test_config = dict(
                test = self,
                test_system = test_system,
                error_code = error_code,
                out_file_name = out_file_name,
                out_directory = dir_+"/out",
                work_directory = dir_ + "/" + self.relative_offset_workdir_,
                test_file_directory = dir_
            )

            for check in self.checks_:
                result = check.executeCheck(test_config, annotations)
                if not result:
                    self.passed_ = False
        else: # skipped
            self._time_end_ = time.perf_counter()
            self.passed_ = True
            # self.ran_ = True
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

        pretty_name = os.path.relpath(self.name_, PROJECT_ROOT_PATH)

        time_taken = self._time_end_ - self._time_start_

        width = test_system.print_width_ - len(prefix) - len(pretty_name) \
              - len(suffix) + cntl_char_pad
        width = max(width, 0)

        suffix = '.' * width + suffix + f" {time_taken:.1g}s"

        message = prefix + pretty_name + suffix

        print(message)

        # if not os.path.exists():

        if not self.postrun_script_ == "":
            script = self.postrun_script_
            script = self.keywordReplace(script)
            preprocess = subprocess.Popen(script,
                                        cwd=dir_,
                                        shell=True,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        universal_newlines=True)

            out, err = preprocess.communicate()
            error_code = preprocess.returncode

            if error_code != 0:
                print('\033[31mERROR: Postrun script for test ' +
                 f'{self.name_}:\n{script}\n failed with:\n' +
                 f'{err}\n' +
                 f'Output:\n{out}' +
                 '\033[0m')
            if self.debug_:
                print("DEBUG: use postrun_script to print useful output here")
                print(out)

        self.ran_ = True

        return "Done"


PyFactory.register(TFCTestObject, "TFCTestObject")
