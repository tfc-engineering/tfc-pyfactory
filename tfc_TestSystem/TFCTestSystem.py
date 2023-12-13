import pathlib

from tfc_PyFactory.InputParameters import InputParameters
file_path = str(pathlib.Path(__file__).parent.resolve()) + "/"

import sys
sys.path.append(file_path + "../")

import tfc_PyFactory
from tfc_PyFactory import *
import TFCTestObject
from TFCTestObject import *

import os
import yaml

import time

# ===================================================================
class TFCTestSystem(TFCObject):
    """Test system to run any type of test with any type of executable.
    The system has a set of input parameters that can be set directly and
    additional options that can be set from a configuration file. By default
    the configuration file will be in the same directory as this file
    and have the name TestSystemCONFIG.yaml (which can be customized)."""
    @staticmethod
    def getInputParameters() -> InputParameters:
        params = TFCObject.getInputParameters()

        params.addRequiredParam("directory", ParameterType.STRING,
                                "The test directory in which to find the tests.")
        params.addRequiredParam("executable", ParameterType.STRING,
                                "The executable to use for the tests (May be overridden).")
        params.addOptionalParam("num_jobs", int(4),
                                "The number of jobs that may run at the same time.")
        params.addOptionalParam("weights", int(1),
                                "Weight classes to allow. "
                                "0=None, "
                                "1=Short, "
                                "2=Intermediate, "
                                "3=Short+Intermediate, "
                                "4=Long, "
                                "5=Long+Short, "
                                "6=Long+Intermediate, "
                                "7=All")
        params.addOptionalParam("config_file", "TestSystemCONFIG.yaml",
                                "The name of the default config file")

        return params


    def __init__(self, params: InputParameters) -> None:
        super().__init__(params)

        # Input parameters
        # AFCF = Also From Config File
        self.directory_ = params.getParam("directory").getStringValue()
        self.executable_ = params.getParam("executable").getStringValue() # AFCF
        self.num_jobs_ = params.getParam("num_jobs").getIntegerValue()
        self.weights_ = params.getParam("weights").getIntegerValue()
        self.config_file_ = params.getParam("config_file").getStringValue()

        # Config file options
        self.print_width_ = 120
        self.default_args_ = ""


        # Init weight map
        weight_class_map = ["long", "intermediate", "short"]
        weight_classes_allowed = []
        if 0 <= self.weights_ <= 7:
            binary_weights = '{0:03b}'.format(self.weights_)
            for k in range(0, 3):
                if binary_weights[k] == '1':
                    weight_classes_allowed.append(weight_class_map[k])
        else:
            raise RuntimeError(
                '\033[31mIllegal value "' + str(self.weights_) + '" supplied ' +
                'for argument -w, --weights\033[0m')

        self.weight_classes_allowed_ = weight_classes_allowed
        self.max_num_procs_ = 1

        self.tests_: list[TFCTestObject] = []

        print("TFCTestSystem created")
        print(f"Main executable: {self.executable_}")
        print(f"Number of jobs : {self.num_jobs_}")
        print(f"Weight classes : {self.weight_classes_allowed_}")

        test_files = self._recursiveFindTestListFiles(self.directory_, True)
        self._parseTestFiles(test_files=test_files)

        for test in self.tests_:
            self.max_num_procs_ = max(self.max_num_procs_, test.num_procs_)

        if os.path.isfile(file_path + self.config_file_):
            with open(file_path + self.config_file_) as yaml_file:
                yaml_dict = yaml.safe_load(yaml_file)

                for param in yaml_dict:
                    if param == "default_executable":
                        self.executable_ = yaml_dict[param]
                    if param == "print_width":
                        self.print_width_ = yaml_dict[param]
                    if param == "default_args":
                        self.default_args_ = yaml_dict[param]

        self._run()


    def _recursiveFindTestListFiles(self, test_dir: str, verbose: bool = False):
        """Recurses through a directory to find *tests*.yaml files"""

        if not os.path.isdir(test_dir):
            raise Exception('"' + test_dir + '" directory does not exist')

        test_files: list[str] = []  # Map of directories to lua files
        for dir_path, sub_dirs, files in os.walk(test_dir):
            for file_name in files:
                base_name, extension = os.path.splitext(file_name)
                if extension == ".yaml" and (base_name.find("tests") > 0):
                    test_files.append(dir_path + file_name)

        if verbose:
            print("Test files identified:\n", test_files)

        return test_files


    def _parseTestFiles(self, test_files: list[str]):
        """Parses each *tests*.yaml file and creates the tests."""
        for file_name in test_files:
            print("Parsing " + file_name)
            with open(file_name) as yaml_file:
                try:
                    yaml_dict = yaml.safe_load(yaml_file)
                    if not yaml_dict:
                        print(f"\033[31mWARNING: Error parsing yaml input \"{file_name}\"\033[0m")
                        continue
                except Exception as ex:
                    print(f"\033[31mWARNING: Error parsing yaml input \"{file_name}\"\033[0m")
                    print(ex)
                    continue

            for test_name in yaml_dict:
                test_dict = yaml_dict[test_name]
                if not isinstance(test_dict, dict):
                    print(f"\033[31mWARNING: Error test \"{test_name}\" is not a dict\033[0m")
                    continue

                dir_, name_ = os.path.split(file_name)
                test_true_name = f'{dir_}/{test_name}'
                test_dict["type"] = "TFCTestObject"

                try:
                    test = PyFactory.makeObject(test_true_name, Parameter("", test_dict))
                    self.tests_.append(test)
                except Exception as ex:
                    print(f"\033[31mWARNING: Error creating test \"{test_name}\"\033[0m\n" +
                          ex.__str__())



    def _run(self):
        """Actually executes the test system"""

        start_time = time.perf_counter()

        job_state = {}
        capacity = self.num_jobs_
        system_load = 0
        active_tests: list[TFCTestObject] = []

        # ======================================= Testing phase
        k = 0
        while True:
            k += 1

            done = True  # Assume we are done
            for test in self.tests_:
                if test.ran_ or (test.weight_class_ not in self.weight_classes_allowed_):
                    continue
                done = False

                if not test.submitted_ and test.checkDependenciesMet(self.tests_):
                    if test.num_procs_ <= (capacity - system_load):
                        system_load += test.num_procs_

                        test.submit(self)

                        active_tests.append(test)

            # Check test progression
            system_load = 0
            for test in active_tests:
                if test.checkProgress(self) == "Running":
                    system_load += test.num_procs_

            time.sleep(0.01)

            if done:
                break # from while-loop

        # ======================================= Post-test phase
        end_time = time.perf_counter()
        elapsed_time = end_time - start_time

        print("Done executing tests with class in: " +
          self.weight_classes_allowed_.__str__())

        num_tests_failed = 0
        for test in active_tests:
            if not test.passed_:
                num_tests_failed += 1

        print()
        print("Elapsed time            : {:.2f} seconds".format(elapsed_time))
        print(f"Number of tests run     : {len(active_tests)}")
        if num_tests_failed == 0:
            print(f"Number of failed tests  : {num_tests_failed}")
        else:
            print(f"\033[31mNumber of failed tests  : {num_tests_failed}\033[0m")

        if num_tests_failed > 0:
            return 1
        return 0






PyFactory.register(TFCTestSystem, "TFCTestSystem")
