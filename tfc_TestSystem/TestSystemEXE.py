#!/usr/bin/env python3

import sys
import os
import argparse

import pathlib
file_path = str(pathlib.Path(__file__).parent.resolve()) + "/"
cwd = os.getcwd()

sys.path.append(file_path + "../")

from tfc_PyFactory import *
from tfc_TestSystem import *
import tfc_TestSystem


# ========================================================= Process commandline
#                                                           arguments
arguments_help = "Runs a test file"

parser = argparse.ArgumentParser(
    description="A script to run a test file.",
    epilog=arguments_help
)

parser.add_argument(
    "-d", "--directory", default=None, type=str, required=True,
    help="The test directory to inspect recursively"
)
parser.add_argument(
    "-e", "--executable", default="python3", type=str, required=False,
    help="The executable to use for the tests (May be overridden)."
)
parser.add_argument(
    "-j", "--num_jobs", default=4, type=int, required=False,
    help="The number of job slots available to run tests"
)
parser.add_argument(
    "-w", "--weights", default=1, type=int, required=False,
    help="Weight classes to allow. "
                                "0=None, "
                                "1=Short, "
                                "2=Intermediate, "
                                "3=Short+Intermediate, "
                                "4=Long, "
                                "5=Long+Short, "
                                "6=Long+Intermediate, "
                                "7=All"
)

argv = parser.parse_args()  # argv = argument values

params: dict = {}
params["type"] = "TFCTestSystem"
params["directory"] = argv.directory
params["executable"] = argv.executable
params["num_jobs"] = argv.num_jobs
params["weights"] = argv.weights

test_system = PyFactory.makeObject("TFCTestSystem", Parameter("", params))
