"""Cookbase Schema Builder

This module processes Cookbase Schema templates and compiles them into the desired
directory structure, either on a local or remote (through SSH) location.

The configuration is taken by default from the :file:`build-config.yaml` file, having
the option to provide a custom configuration file by using the
:option:`-c`/:option:`--config` command-line option. Any mandatory parameters lacking in
the custom coniguration file are directly taken from the default values.

"""
import argparse
import bisect
import json
import os
import string
from collections import OrderedDict
from typing import Any, Dict

import paramiko
import uritools
from cookbase.utils import _HelpAction, _SortingDict
from paramiko.client import SSHClient
from ruamel.yaml import YAML


class _SSHConnection:
    """Helper class handling SFTP communication.

    If provided with a hostname, automatically initiates the SFTP session.

    :param hostname: The SSH host, defaults to :const:`None`
    :type hostname: str, optional
    :param port: The port where the SSH host is listening, defaults to :const:`None`
    :type port: int, optional
    :param username: The username on the target SSH host, defaults to :const:`None`
    :type username: str, optional

    :ivar client: The SSH session handler
    :vartype client: paramiko.client.SSHClient
    :ivar sftp_session: The SFTP session handler
    :vartype sftp_session: paramiko.sftp_client.SFTPClient
    """

    client = None
    sftp_session = None

    def __init__(self, hostname: str = None, port: int = None, username: str = None):
        """Constructor method."""
        if hostname:
            self.set_session(hostname, port, username)

    def set_session(self, hostname: str, port: int = None, username: str = None):
        """
        Sets up a SFTP session.

        :param str hostname: The SSH host
        :param port: The port where the SSH host is listening, defaults to :const:`None`
        :type port: int, optional
        :param username: The username on the target SSH host, defaults to :const:`None`
        :type username: str, optional
        """
        self.client = SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        if port and username:
            self.client.connect(hostname, port, username)
        elif port:
            self.client.connect(hostname, port)
        elif username:
            self.client.connect(hostname, username=username)
        else:
            self.client.connect(hostname)

        self.sftp_session = self.client.open_sftp()

    def close_session(self):
        """
        Closes the SFTP session.
        """
        if self.is_active():
            self.client.close()

    def mkdir_p(self, path: str):
        """
        Simulates the :command:`mkdir -p <path>` Unix command, making a directory and
        all its non-existing parent directories.

        :param str path: The path to a directory
        """
        dirs = []

        while len(path) > 1:
            dirs.append(path)
            path = os.path.dirname(path)

        if len(path) == 1 and not path.startswith("/"):
            dirs.append(path)

        while len(dirs):
            path = dirs.pop()
            try:
                self.sftp_session.stat(path)
            except:
                self.sftp_session.mkdir(path, mode=0o755)

    def write_file(self, s: str, path: str):
        """
        Creates or overwrites a file under `path` and stores the content of `s` in it.

        :param str s: String to be written into a new file
        :param path: Path to the new file
        """
        self.mkdir_p(os.path.normpath(os.path.dirname(path)))
        sftp_file = self.sftp_session.open(path, "w")
        sftp_file.write(s)
        sftp_file.close()

    def is_active(self):
        """
        Checks whether the SSH session is active or not.
        """
        if self.client:
            transport = self.client.get_transport()

            if transport is not None and transport.is_active():
                try:
                    transport.send_ignore()
                    return True
                except EOFError:
                    return False

        return False


config = None
ssh = None


def build_abs_schema_uri(rel_path: str):
    """
    It forms an absolute URI from a relative path considering the
    :code:`common.cb_schemas_base_url` property provided by the build configuration
    file.

    :param str rel_path: A path relative to :code:`build_params.root_build_dir`
    :return: An absolute URI intended to unambiguously refer to the given path
    :rtype: str
    """
    base_url_splits = uritools.urisplit(config["common"]["cb_schemas_base_url"])

    abs_path = base_url_splits.path

    if abs_path == "":
        abs_path = "/"

    return uritools.urijoin(
        config["common"]["cb_schemas_base_url"], os.path.join(abs_path, rel_path)
    )


def build_rel_path(start_rel_path: str, target_rel_path: str):
    """
    Calculates the relative path from `start_rel_path` to `target_rel_path`.

    :param str start_rel_path: The startpoint path
    :param str target_rel_path: The target path
    :return: A relative path from `start_rel_path` to `target_rel_path`
    :rtype: str
    """
    base_path = uritools.urisplit(config["build_params"]["root_build_dir"]).path
    start_path = os.path.dirname(os.path.join(base_path, start_rel_path))
    target_path = os.path.join(base_path, target_rel_path)

    return os.path.relpath(target_path, start_path)


def write_to_file(s: str, path: str):
    """
    Creates or overwrites a file (either locally or remotely) and stores `s` in it.

    :param str s: The string to be written in the file
    :param str path: The path where the file is to be created
    """
    if ssh:
        ssh.write_file(s, path)
    else:
        os.makedirs(os.path.dirname(path), mode=0o755, exist_ok=True)
        with open(path, "w") as f:
            f.write(s)


def render(template_filename: str, schema_path: str, substs: Dict[str, str]):
    """
    Creates a JSON Schema file under `schema_path` from applying the substitutions
    `substs` to a template stored in `template_filename`.

    :param str template_filename: The name of the template file to be rendered
    :param str schema_path: The path where the generated JSON Schema will be stored
    :param substs: A dictionary including the substitutions to be performed on the
      template
    :type substs: Dict[str, str]
    """
    with open(
        os.path.join(
            config["build_params"]["cb_schema_templates_dir"], template_filename
        )
    ) as f:
        template = string.Template(f.read())

    schema = template.substitute(substs)
    path = os.path.join(
        uritools.urisplit(config["build_params"]["root_build_dir"]).path, schema_path
    )
    write_to_file(schema, path)


def build_cb_common_definitions_schema():
    """
    Builds the CB Common Definitions Schema according to the provided configuration.
    """
    substs = {
        "json_schema_uri": config["common"]["json_schema_uri"],
        "cb_common_definitions_url": build_abs_schema_uri(
            config["common"]["defs_path"]
        ),
    }

    render("cb-common-definitions.template.json", config["common"]["defs_path"], substs)


def build_cbr_schema(build_cbr_process: bool = True):
    """
    Builds the CBR Schema according to the provided configuration.

    If the `build_cbr_process` flag is set to :const:`True` (the default), this
    function will also build CBR Process Schema.

    :param build_cbr_process: Flag indicating whether the CBR Process Schema will be
      generated or not
    :type build_cbr_process: bool, optional
    """
    # Build CBR main schema
    substs = {
        "json_schema_uri": config["common"]["json_schema_uri"],
        "cbr_schema_url": build_abs_schema_uri(
            config["build_params"]["cbr_schema_path"]
        ),
        "common_defs_path": build_rel_path(
            config["build_params"]["cbr_schema_path"], config["common"]["defs_path"]
        ),
    }

    for k, v in config["cbr"].items():
        substs[k] = build_rel_path(config["build_params"]["cbr_schema_path"], v)

    render("cbr.template.json", config["build_params"]["cbr_schema_path"], substs)

    # Build CBR-info schema
    substs = {
        "json_schema_uri": config["common"]["json_schema_uri"],
        "cbr_info_schema_url": build_abs_schema_uri(config["cbr"]["cbr_info_path"]),
        "common_defs_path": build_rel_path(
            config["cbr"]["cbr_info_path"], config["common"]["defs_path"]
        ),
    }

    render("cbr-info.template.json", config["cbr"]["cbr_info_path"], substs)

    # Build CBR-yield schema
    substs = {
        "json_schema_uri": config["common"]["json_schema_uri"],
        "cbr_yield_schema_url": build_abs_schema_uri(config["cbr"]["cbr_yield_path"]),
        "common_defs_path": build_rel_path(
            config["cbr"]["cbr_yield_path"], config["common"]["defs_path"]
        ),
    }

    render("cbr-yield.template.json", config["cbr"]["cbr_yield_path"], substs)

    # Build CBR-ingredient schema
    substs = {
        "json_schema_uri": config["common"]["json_schema_uri"],
        "cbr_ingredient_schema_url": build_abs_schema_uri(
            config["cbr"]["cbr_ingredient_path"]
        ),
        "common_defs_path": build_rel_path(
            config["cbr"]["cbr_ingredient_path"], config["common"]["defs_path"]
        ),
    }

    render("cbr-ingredient.template.json", config["cbr"]["cbr_ingredient_path"], substs)

    # Build CBR-appliance schema
    substs = {
        "json_schema_uri": config["common"]["json_schema_uri"],
        "cbr_appliance_schema_url": build_abs_schema_uri(
            config["cbr"]["cbr_appliance_path"]
        ),
        "common_defs_path": build_rel_path(
            config["cbr"]["cbr_appliance_path"], config["common"]["defs_path"]
        ),
    }

    render("cbr-appliance.template.json", config["cbr"]["cbr_appliance_path"], substs)

    if build_cbr_process:
        build_cbr_process_schema()


def build_cbi_schema():
    """
    Builds the CBI Schema according to the provided configuration.
    """
    substs = {
        "json_schema_uri": config["common"]["json_schema_uri"],
        "cbi_schema_url": build_abs_schema_uri(
            config["build_params"]["cbi_schema_path"]
        ),
        "common_defs_path": build_rel_path(
            config["build_params"]["cbi_schema_path"], config["common"]["defs_path"]
        ),
    }

    render("cbi.template.json", config["build_params"]["cbi_schema_path"], substs)


def build_cba_schema():
    """
    Builds the CBA Schema according to the provided configuration.
    """
    substs = {
        "json_schema_uri": config["common"]["json_schema_uri"],
        "cba_schema_url": build_abs_schema_uri(
            config["build_params"]["cba_schema_path"]
        ),
        "common_defs_path": build_rel_path(
            config["build_params"]["cba_schema_path"], config["common"]["defs_path"]
        ),
    }

    render("cba.template.json", config["build_params"]["cba_schema_path"], substs)


def build_cbp_schema():
    """
    Builds the CBP Schema according to the provided configuration.
    """
    substs = {
        "json_schema_uri": config["common"]["json_schema_uri"],
        "cbp_schema_url": build_abs_schema_uri(
            config["build_params"]["cbp_schema_path"]
        ),
        "common_defs_path": build_rel_path(
            config["build_params"]["cbp_schema_path"], config["common"]["defs_path"]
        ),
    }

    render("cbp.template.json", config["build_params"]["cbp_schema_path"], substs)


def build_caf_schema():
    """
    Builds the CAF Schema according to the provided configuration.
    """
    substs = {
        "json_schema_uri": config["common"]["json_schema_uri"],
        "caf_schema_url": build_abs_schema_uri(
            config["build_params"]["caf_schema_path"]
        ),
        "common_defs_path": build_rel_path(
            config["build_params"]["caf_schema_path"], config["common"]["defs_path"]
        ),
    }

    render("caf.template.json", config["build_params"]["caf_schema_path"], substs)


def build_cbr_process_schema(do_collection: bool = True):
    """
    Builds the CBR Process Schema according to the provided configuration.

    If the `do_collection` flag is set to :const:`True` (the default), the
    function will builds CBR Process Schemas collection.

    :param do_collection: Flag indicating whether the CBR Process Schemas collection
      will be generated or not.
    :type do_collection: bool, optional
    """
    build_cbr_process_definitions_schema()

    if do_collection:
        generate_cbr_process_collection()

    generate_cbr_process_main_schema()


def build_cbr_process_definitions_schema():
    """
    Builds the CBR Process Definitions Schema according to the provided configuration.
    """
    substs = {
        "json_schema_uri": config["common"]["json_schema_uri"],
        "cbr_process_definitions_url": build_abs_schema_uri(
            config["cbr_process"]["defs_path"]
        ),
    }

    render(
        "cbr-process-definitions.template.json",
        config["cbr_process"]["defs_path"],
        substs,
    )


def generate_cbr_process_collection():
    """
    Generates and writes into files the CBR Process Schemas from a collection of CBP
    files.

    The accessed CBP files are under the directory specified by the
    :code:`cbr_process.cbp_dir` property from the build configuration file.

    The routes to the JSON Schema definitions of the different :code:`type`\ s referred
    by the CBP documents are detailed in the configuration file under the path given by
    the :code:`cbr_process.types_path` property.
    """

    with open(config["cbr_process"]["types_path"]) as f:
        d = YAML().load(f)

    def build_ref(entry):
        return uritools.urijoin(
            build_rel_path(
                os.path.join(
                    config["build_params"]["cbr_process_collection_dir"], "dummy"
                ),
                config[entry["ns"]]["defs_path"],
            ),
            f'#{entry["def"]}',
        )

    defs = {i: build_ref(d[i]) for i in d.keys()}

    for filename in os.listdir(config["cbr_process"]["cbp_dir"]):
        if os.path.splitext(filename)[1] == ".cbp":
            with open(os.path.join(config["cbr_process"]["cbp_dir"], filename)) as f:
                cbp = json.load(f, object_pairs_hook=OrderedDict)

            if cbp["data"]["processType"] != "generic":
                continue

            schema_filename = filename.rsplit("-", 1)[0].replace(" ", "_") + ".json"
            schema = generate_cbr_process_collection_item(cbp, defs, schema_filename)
            path = os.path.join(
                uritools.urisplit(config["build_params"]["root_build_dir"]).path,
                config["build_params"]["cbr_process_collection_dir"],
                filename.rsplit("-", 1)[0] + ".json",
            )

            write_to_file(json.dumps(schema, indent=2), path)


def generate_cbr_process_collection_item(
    cbp: Dict[str, Any], defs: Dict[str, str], schema_filename: str = None
):
    """
    Generates and writes into a file a CBR Process Schema from a CBP document.

    If `schema_filename` is set to :const:`None` (the default), the output file name
    will be assumed to be the first English name given in the CBP's :code:`name`
    property, lowercased, substituted spaces by underscores :const:`_`, and appended the
    :code:`.json` extension.

    :param cbp: The dictionary representing the content of a CBP document
    :type cbp: dict[str, Any]
    :param defs: A dictionary mapping the CBP
      :code:`data.schema.foodstuffKeywords.*.type` properties to the location of its
      definition
    :type defs: dict[str, str]
    :param schema_filename: The name of the file where the CBP is to be stored,
      defaults to :const:`None`
    :type schema_filename: str, optional
    """
    # It assumes a valid CBP
    if cbp["data"]["processType"] != "generic":
        raise ValueError

    # Get CBP name
    process_name = cbp["name"]["en"]

    if isinstance(process_name, list):
        process_name = process_name[0]

    if not schema_filename:
        schema_filename = process_name.lower().replace(" ", "_")

    schema = OrderedDict()
    schema["$schema"] = config["common"]["json_schema_uri"]
    schema["$id"] = build_abs_schema_uri(
        os.path.join(
            config["build_params"]["cbr_process_collection_dir"], schema_filename
        )
    )
    schema["title"] = 'Cookbase Recipe Process "' + process_name + '"'
    schema[
        "description"
    ] = f'Schema defining the format of the CBR "{process_name}" Process.'
    schema["type"] = "object"
    schema["additionalProperties"] = False
    schema["required"] = ["name", "cbpId"]
    schema["properties"] = OrderedDict(
        [("name", {"$ref": defs["name"]}), ("cbpId", {"const": cbp["id"]})]
    )

    # Generate parameters property
    parameters_is_required = False

    if cbp["data"]["schema"].get("parameters"):
        schema["properties"]["parameters"] = OrderedDict(
            [("type", "object"), ("additionalProperties", False)]
        )

        required_params = []
        properties_params = OrderedDict()

        for p, v in cbp["data"]["schema"]["parameters"].items():
            if p == "endConditions":
                properties_params["endConditions"] = OrderedDict(
                    [("type", "object"), ("additionalProperties", False)]
                )

                required_ec = []
                properties_ec = OrderedDict()

                for ec, v_ec in v.items():
                    if v_ec["required"]:
                        parameters_is_required = False
                        required_ec.append(ec)

                    properties_ec[ec] = {"$ref": defs[ec]}

                if required_ec:
                    properties_params["endConditions"]["required"] = required_ec

                properties_params["endConditions"]["properties"] = properties_ec

            else:
                if v["required"]:
                    parameters_is_required = False
                    required_params.append(p)

                properties_params[p] = {"$ref": defs[p]}

        if required_params:
            schema["properties"]["parameters"]["required"] = required_params

        if cbp["data"]["schema"].get("minParameters"):
            schema["properties"]["parameters"]["minProperties"] = cbp["data"][
                "schema"
            ].get("minParameters")

        schema["properties"]["parameters"]["properties"] = properties_params

    if parameters_is_required:
        schema["required"].append("parameters")

    # Generate foodstuff properties
    for f, v in cbp["data"]["schema"]["foodstuffKeywords"].items():
        if v["required"]:
            schema["required"].append(f)

        schema["properties"][f] = {"$ref": defs[v["type"]]}

    # Generate appliances property
    schema["required"].append("appliances")
    schema["properties"]["appliances"] = {"$ref": defs["appliances"]}

    if cbp["data"]["schema"].get("flags"):
        for f in cbp["data"]["schema"]["flags"]:
            schema["required"].append(f)
            schema["properties"][f] = {"const": True}

    schema["properties"]["notes"] = {"$ref": defs["notes"]}

    return schema


def generate_cbr_process_main_schema():
    """
    Generates and writes into file the CBR Process Main Schema from a collection of CBR
    Process Schemas.

    Its path is provided by the :code:`cbr.cbr_process_path` property in the build
    configuration file.
    """
    schema = OrderedDict()
    schema["$schema"] = config["common"]["json_schema_uri"]
    schema["$id"] = build_abs_schema_uri(config["cbr"]["cbr_process_path"])
    schema["title"] = "Cookbase Recipe Process - v1.0"
    schema["description"] = (
        "Schema defining the format of the Cookbase Recipe (CBR) Process. Visit "
        "https://cookbase.readthedocs.io/en/latest/cbdm.html#cbr-preparation to read "
        "the documentation."
    )
    schema["oneOf"] = []
    collection_base_path = os.path.join(
        uritools.urisplit(config["build_params"]["root_build_dir"]).path,
        config["build_params"]["cbr_process_collection_dir"],
    )

    def enter_ref(p):
        return bisect.insort(
            schema["oneOf"],
            _SortingDict(
                {
                    "$ref": build_rel_path(
                        config["cbr"]["cbr_process_path"],
                        os.path.join(collection_base_path, p),
                    )
                }
            ),
        )

    if ssh:
        for p in ssh.sftp_session.listdir(collection_base_path):
            if os.path.splitext(p)[1] == ".json":
                enter_ref(p)
    else:
        for p in os.listdir(collection_base_path):
            if os.path.splitext(p)[1] == ".json":
                enter_ref(p)

    path = os.path.join(
        uritools.urisplit(config["build_params"]["root_build_dir"]).path,
        config["cbr"]["cbr_process_path"],
    )

    write_to_file(json.dumps(schema, indent=2), path)


def init(config_path: str = None):
    """
    Initializes the builder.

    If a custom build configuration file `config_path` is not provided, the default
    build configuration is loaded; if provided, any lacking parameter will be completed
    with the default configuration.

    In case of a :code:`build_params.root_build_dir` configuration property consisting
    of a SSH or SFTP URI, a SFTP session with the target host is opened.

    :param config_path: Path to the custom build configuration file, defaults to
      :const:`None`
    :type config_path: str, optional
    """
    global config, ssh

    with open("./build-config.yaml") as f:
        config = YAML().load(f)

    if config_path:

        def update(d, u):
            import collections.abc

            for k, v in u.items():
                if isinstance(v, collections.abc.Mapping):
                    d[k] = update(d.get(k, {}), v)
                else:
                    d[k] = v
            return d

        with open(config_path) as f:
            custom_config = YAML().load(f)

        config = update(config, custom_config)

    splits = uritools.urisplit(config["build_params"]["root_build_dir"])

    if splits.getscheme() == "ssh" or splits.getscheme() == "sftp":
        ssh = _SSHConnection(
            str(splits.gethost()), splits.getport(22), splits.getuserinfo()
        )
    elif not splits.getscheme("file") == "file":
        raise ValueError


def closedown():
    """
    Terminates the builder.
    """
    if ssh:
        ssh.close_session()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Cookbase Schema Builder", add_help=False)
    ap.add_argument(
        "-h", "--help", action=_HelpAction, help="show this help message and exit"
    )
    ap.add_argument("-c", "--config", help="path to the build configuration file")
    args = ap.parse_args()
    init(args.config)
    build_cb_common_definitions_schema()
    build_cbr_schema()
    build_cbi_schema()
    build_cba_schema()
    build_cbp_schema()
    build_caf_schema()
    closedown()
