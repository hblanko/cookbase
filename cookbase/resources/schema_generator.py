import argparse
import bisect
import json
from collections import OrderedDict
import os
import tempfile
from typing import Any, Dict

import paramiko
from paramiko.client import SSHClient

from cookbase.parsers.jsonfoodex import _HelpAction


class _SortingDict(dict):
    def __init__(self, mapping=(), **kwargs):
        super(_SortingDict, self).__init__(mapping, **kwargs)

    def __lt__(self, other):
        return self["$ref"] < other["$ref"]


def generate_cbp_json_schema(
        cbp: Dict[str, Any]) -> Dict[str, Any]:
    # It assumes a valid CBP
    if cbp['data']['processType'] != 'generic':
        raise ValueError

    definitions = {
        'descriptive': '../cb-global-definitions.json#/textWithLanguage',
        'ovenPosition': '../cb-global-definitions.json#/quantities/descriptive/height',
        'pieces': '../cb-global-definitions.json#/positiveInteger',
        'size': '../cb-global-definitions.json#/quantities/length',
        'temperature': '../cb-global-definitions.json#/quantities/temperature',
        'time': '../cb-global-definitions.json#/quantities/time',
        'weight': '../cb-global-definitions.json#/quantities/mass',
        'foodstuff': '../process-schema.json#/definitions/foodstuff',
        'foodstuffsList': '../process-schema.json#/definitions/foodstuffsList'
    }

    # Get CBP name
    process_name = cbp['name']['en']
    if isinstance(process_name, list):
        process_name = process_name[0]

    schema = OrderedDict()
    schema['$schema'] = 'http://json-schema.org/draft-07/schema#'
    schema['$id'] = 'https://landarltracker.com/schemas/processes/' + \
        process_name + '.json'
    schema['title'] = 'Process \'' + process_name + '\''
    schema['description'] = 'Schema defining the format of the \'' + \
        process_name + '\' process.'
    schema['type'] = 'object'
    schema['additionalProperties'] = False
    schema['required'] = ['name', 'cbpId']
    schema['properties'] = OrderedDict([('name', {'$ref': '../cb-global-definitions.json#/textWithLanguage'}),
                                        ('cbpId', {'const': cbp['id']})])

    # Generate parameters property
    parameters_is_required = False

    if cbp['data']['schema'].get('parameters'):
        schema['properties']['parameters'] = OrderedDict([('type', 'object'),
                                                          ('additionalProperties', False)])

        required_params = list()
        properties_params = OrderedDict()

        for p, v in cbp['data']['schema']['parameters'].items():
            if p == 'endConditions':
                properties_params['endConditions'] = OrderedDict([('type', 'object'),
                                                                  ('additionalProperties', False)])

                required_ec = list()
                properties_ec = OrderedDict()

                for ec, v_ec in v.items():
                    if v_ec['required']:
                        parameters_is_required = False
                        required_ec.append(ec)

                    properties_ec[ec] = {'$ref': definitions[ec]}

                if required_ec:
                    properties_params['endConditions']['required'] = required_ec

                properties_params['endConditions']['properties'] = properties_ec

            else:
                if v['required']:
                    parameters_is_required = False
                    required_params.append(p)

                properties_params[p] = {'$ref': definitions[p]}

        if required_params:
            schema['properties']['parameters']['required'] = required_params

        if cbp['data']['schema'].get('minParameters'):
            schema['properties']['parameters']['minProperties'] = cbp['data']['schema'].get(
                'minParameters')

        schema['properties']['parameters']['properties'] = properties_params

    if parameters_is_required:
        schema['required'].append('parameters')

    # Generate foodstuff properties
    for f, v in cbp['data']['schema']['foodstuffKeywords'].items():
        if v['required']:
            schema['required'].append(f)

        schema['properties'][f] = {'$ref': definitions[v['type']]}

    # Generate appliances property
    schema['required'].append('appliances')
    schema['properties']['appliances'] = {
        '$ref': '../process-schema.json#/definitions/appliances'}

    if cbp['data']['schema'].get('flags'):
        for f in cbp['data']['schema']['flags']:
            schema['required'].append(f)
            schema['properties'][f] = {'const': True}

    schema['properties']['notes'] = {
        '$ref': '../cb-global-definitions.json#/notes'}

    return schema


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description="Cookbase Schema Compiler",
                                 add_help=False)
    ap.add_argument('-h', '--help', action=_HelpAction,
                    help='show this help message and exit')
    subparsers = ap.add_subparsers(dest="command")
    subparsers.required = True
    parsexml_parser = subparsers.add_parser(
        "process", help="generate 'process.json' Cookbase JSON Schema")
    parsexml_parser.add_argument(
        "schemadir", help="path to the schema directory")
    parsexml_parser.add_argument(
        "-r",
        "--remote",
        help="provide a <user>@<host> SSH connection to access the schema directory")
    parsexml_parser.add_argument(
        "-i",
        "--input",
        help="path (either to a file or directory) to the CBP data")
    args = ap.parse_args()

    if args.remote:
        client = SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            args.remote.split("@")[1],
            username=args.remote.split("@")[0])
        sftp = client.open_sftp()

    if args.input:
        if os.path.isdir(args.input):
            for e in os.scandir(args.input):
                if e.path.endswith(".cbp"):
                    with open(e.path) as f:
                        cbp = json.load(f, object_pairs_hook=OrderedDict)

                        if cbp['data']['processType'] != 'generic':
                            continue

                        schema = generate_cbp_json_schema(cbp)

                        if args.remote:
                            with tempfile.TemporaryFile("w+") as tmp:
                                json.dump(schema, tmp, indent=2)
                                tmp.flush()
                                tmp.seek(0)
                                sftp.putfo(
                                    tmp,
                                    args.schemadir +
                                    "/processes/" +
                                    e.name.rsplit(
                                        '-',
                                        1)[0] +
                                    '.json')

                        else:
                            with open(args.schemadir + "/processes/" + e.name.rsplit('-', 1)[0] + '.json', "w") as p:
                                json.dump(schema, p, indent=2)

        else:
            with open(args.input) as f:
                cbp = json.load(f, object_pairs_hook=OrderedDict)

                if cbp['data']['processType'] != 'generic':
                    print(
                        'WARNING: parsing will fail due to a not \'generic\'-typed CBP')

                schema = generate_cbp_json_schema(cbp)
                input_filename = args.input.rsplit('/', 1)[1]

                if args.remote:
                    with tempfile.TemporaryFile("w+") as tmp:
                        json.dump(schema, tmp, indent=2)
                        tmp.flush()
                        tmp.seek(0)
                        sftp.putfo(
                            tmp,
                            args.schemadir +
                            "/processes/" +
                            input_filename.rsplit(
                                '-',
                                1)[0] +
                            '.json')

                else:
                    with open(args.schemadir + "/processes/" + input_filename.rsplit('-', 1)[0] + '.json', "w") as p:
                        json.dump(schema, p, indent=2)

    process = OrderedDict()
    process["$schema"] = "http://json-schema.org/draft-07/schema#"
    process["$id"] = "https://landarltracker.com/schemas/process.json"
    oneOf = list()

    if args.remote:
        for p in sftp.listdir(args.schemadir + "/processes"):
            if p.endswith(".json"):
                bisect.insort(oneOf, _SortingDict({"$ref": "processes/" + p}))

    else:
        for e in os.scandir(args.schemadir + "/processes"):
            if e.path.endswith(".json"):
                bisect.insort(oneOf, _SortingDict(
                    {"$ref": "processes/" + e.name}))

    process["oneOf"] = oneOf

    if args.remote:
        with tempfile.TemporaryFile("w+") as tmp:
            json.dump(process, tmp, indent=2)
            tmp.flush()
            tmp.seek(0)
            sftp.putfo(tmp, args.schemadir + "/process.json")

        client.close()
    else:
        with open(args.schemadir + "/process.json", "w") as f:
            json.dump(process, f, indent=2)
