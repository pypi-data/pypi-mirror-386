######################################################################################
# Copyright (c) 2023-2025 Orange. All rights reserved.                               #
# This software is distributed under the BSD 3-Clause-clear License, the text of     #
# which is available at https://spdx.org/licenses/BSD-3-Clause-Clear.html or         #
# see the "LICENSE.md" file for more details.                                        #
######################################################################################
"""Khiops Python samples
The functions in this script demonstrate the basic use of the khiops library.

This script is fully compatible with the latest Khiops version. If you are using an
older version some samples may fail.
"""
import argparse
import io

import khiops
import os
from khiops import core as kh
from khiops.core import KhiopsOutputWriter


# Disable open files without encoding because samples are simple code snippets
# pylint: disable=unspecified-encoding

# For ease of use the functions in this module contain (repeated) import statements
# We disable all pylint warnings related to imports
# pylint: disable=import-outside-toplevel,redefined-outer-name,reimported


def create_dictionary():
    """Creates a dictionary file from scratch
    with all the possible variable types
    """
    # Imports
    import os
    from khiops import core as kh

    # Creates a Root dictionary
    root_dictionary = kh.Dictionary(json_data={"name": "dict_from_scratch",
                                               "root": True,
                                               "key": ["Id"]})

    # Starts with simple variables to declare
    simple_variables = [
        {"name": "Id", "type": "Categorical"},
        {"name": "Num", "type": "Numerical"},
        {"name": "text", "type": "Text"},
        {"name": "hour", "type": "Time"},
        {"name": "date", "type": "Date"},
        {"name": "ambiguous_ts", "type": "Timestamp"},
        {"name": "ts", "type": "TimestampTZ"},
    ]
    for var_spec in simple_variables:
        var = kh.Variable()
        var.name = var_spec["name"]
        var.type = var_spec["type"]
        root_dictionary.add_variable(var)

    # Creates a related second dictionary
    second_dictionary = kh.Dictionary(json_data={"name": "Service",
                                                 "key": ["Id", "id_product"]})
    second_dictionary.add_variable(kh.Variable(json_data={"name": "Id",
                                                          "type": "Categorical"}))
    second_dictionary.add_variable(kh.Variable(json_data={"name": "id_product",
                                                          "type": "Categorical"}))

    # Creates a related third dictionary
    third_dictionary = kh.Dictionary(json_data={"name": "Address",
                                                "key": ["Id"]})
    third_dictionary.add_variable(kh.Variable(json_data={"name": "StreetNumber",
                                                         "type": "Numerical"}))
    third_dictionary.add_variable(kh.Variable(json_data={"name": "StreetName",
                                                         "type": "Categorical"}))
    third_dictionary.add_variable(kh.Variable(json_data={"name": "id_city",
                                                         "type": "Categorical"}))

    # Adds the variables used in a Multi-tables context in the first dictionary
    root_dictionary.add_variable(kh.Variable(json_data={"name": "Services",
                                                        "type": "Table(Service)"}))
    root_dictionary.add_variable(kh.Variable(json_data={"name": "Address",
                                                        "type": "Entity(Address)"}))

    # Creates a DictionaryDomain (set of dictionaries)
    dictionary_domain = kh.DictionaryDomain()
    dictionary_domain.add_dictionary(root_dictionary)
    dictionary_domain.add_dictionary(second_dictionary)
    dictionary_domain.add_dictionary(third_dictionary)

    output_dir = os.path.join("kh_samples", "create_dictionary")
    dictionary_file_path = os.path.join(output_dir, "dict_from_scratch.kdic")

    # Create the output directory if needed
    if not os.path.isdir(output_dir):
        os.mkdir(output_dir)

    # Writes the dictionary domain
    with open(dictionary_file_path, "w") as report_file:
        report_file_writer = KhiopsOutputWriter(report_file)
        dictionary_domain.write(report_file_writer)


exported_samples = [
   create_dictionary,
]

def execute_samples(args):
    """Executes all non-interactive samples"""
    # Create the results directory if it does not exist
    if not os.path.isdir("./kh_samples"):
        os.mkdir("./kh_samples")

    # Set the user-defined samples dir if any
    if args.samples_dir is not None:
        kh.get_runner().samples_dir = args.samples_dir

    # Filter the samples according to the options
    if args.include is not None:
        execution_samples = filter_samples(
            exported_samples, args.include, args.exact_match
        )
    else:
        execution_samples = exported_samples

    # Print the execution title
    if execution_samples:
        print(f"Khiops Python library {khiops.__version__} running on Khiops ", end="")
        print(f"{kh.get_khiops_version()}\n")
        print(f"Sample datasets location: {kh.get_samples_dir()}")
        print(f"{len(execution_samples)} sample(s) to execute\n")

        for sample in execution_samples:
            print(f">>> Executing samples.{sample.__name__}")
            sample.__call__()
            print("> Done\n")

        print("*** Samples run! ***")

    else:
        print("*** No samples to run ***")


def filter_samples(sample_list, include, exact_match):
    """Filter the samples according to the command line options"""
    filtered_samples = []
    for sample in sample_list:
        for sample_name in include:
            if (exact_match and sample_name == sample.__name__) or (
                    not exact_match and sample_name in sample.__name__
            ):
                filtered_samples.append(sample)

    return filtered_samples

def build_argument_parser(prog, description):
    """Samples argument parser builder function

    Parameters
    ----------
    prog : str
        Name of the program, as required by the argument parser.
    description : str
        Description of the program, as required by the argument parser.

    Returns
    -------
    ArgumentParser
        Argument parser object.
    """
    parser = argparse.ArgumentParser(
        prog=prog,
        formatter_class=argparse.RawTextHelpFormatter,
        description=description,
    )
    parser.add_argument(
        "-d",
        "--samples-dir",
        metavar="URI",
        help="Location of the Khiops 'samples' directory",
    )
    parser.add_argument(
        "-i", "--include", nargs="*", help="Executes only the tests matching this list"
    )
    parser.add_argument(
        "-e",
        "--exact-match",
        action="store_true",
        help="Matches with --include are exact",
    )
    return parser


# Run the samples if executed as a script
if __name__ == "__main__":
    argument_parser = build_argument_parser(
        prog="python samples.py",
        description=(
            "Examples of use of the core submodule of the Khiops Python library"
        ),
    )
    execute_samples(argument_parser.parse_args())
