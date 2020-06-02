"""Module that parses the command-line arguments."""
import argparse

import cookbase
from cookbase.utils import _HelpAction


def parse_cli():
    """Parse the arguments provided for the package execution."""
    parser = argparse.ArgumentParser(
        prog="cookbase", description="The Cookbase Platform", add_help=False
    )
    parser.add_argument(
        "-h", "--help", action=_HelpAction, help="show this help message and exit"
    )
    subparsers = parser.add_subparsers(help="available commands")

    parser_builder = subparsers.add_parser(
        "schema-builder", help="Cookbase Schema Builder"
    )
    parser_builder.add_argument(
        "-c",
        "--config",
        dest="config_path",
        help="path to the custom configuration file",
    )
    parser_builder.set_defaults(func=cookbase.schema.builder.main)

    args = parser.parse_args()
    args.func(args)


parse_cli()
