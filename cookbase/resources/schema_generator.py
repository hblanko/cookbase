import argparse
import bisect
import json
from collections import OrderedDict
import os
import tempfile

import paramiko
from paramiko.client import SSHClient

from cookbase.parsers.jsonfoodex import _HelpAction


class _SortingDict(dict):
    def __init__(self, mapping=(), **kwargs):
        super(_SortingDict, self).__init__(mapping, **kwargs)

    def __lt__(self, other):
        return self["$ref"] < other["$ref"]


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description="Cookbase Schema Generator",
                                 add_help=False)
    ap.add_argument('-h', '--help', action=_HelpAction,
                    help='show this help message and exit')
    subparsers = ap.add_subparsers(dest="command")
    subparsers.required = True
    parsexml_parser = subparsers.add_parser(
        "process", help="generate 'process.json' Cookbase JSON Schema")
    parsexml_parser.add_argument(
        "schemafolder", help="path to the schema directory")
    parsexml_parser.add_argument(
        "-r",
        "--remote",
        help="provide a <user>@<host> SSH connection")
    args = ap.parse_args()

    process = OrderedDict()
    process["$schema"] = "http://json-schema.org/draft-07/schema#"
    process["$id"] = "http://www.landarltracker.com/schemas/process.json"
    oneOf = list()

    if args.remote:
        client = SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            args.remote.split("@")[1],
            username=args.remote.split("@")[0])
        sftp = client.open_sftp()

        for p in sftp.listdir(args.schemafolder + "/processes"):
            if p.endswith(".json"):
                bisect.insort(oneOf, _SortingDict({"$ref": "processes/" + p}))

    else:
        for e in os.scandir(args.schemafolder + "/processes"):
            if e.path.endswith(".json"):
                bisect.insort(oneOf, _SortingDict(
                    {"$ref": "processes/" + e.name}))

    process["oneOf"] = oneOf

    if args.remote:
        with tempfile.TemporaryFile("w+") as tmp:
            json.dump(process, tmp, indent=2)
            tmp.flush()
            tmp.seek(0)
            sftp.putfo(tmp, args.schemafolder + "/process.json")

        client.close()
    else:
        with open(args.schemafolder + "/process.json", "w") as f:
            json.dump(process, f, indent=2)
