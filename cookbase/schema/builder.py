"""
Cookbase Schema Builder.

This module processes Cookbase Schema templates and compiles them into the desired
directory structure, either on a local or remote (through SSH) location.

The configuration is taken by default from the :file:`build-config.yaml` file, having
the option to provide a custom configuration file. Any mandatory parameters lacking in
the custom configuration file are directly taken from the default values.
"""
import bisect
import json
import os
import string
import tempfile
from argparse import Namespace
from collections import OrderedDict
from collections.abc import Mapping
from typing import Any, Dict, Tuple

import paramiko
import uritools
from paramiko.client import SSHClient
from ruamel.yaml import YAML

from cookbase.utils import _SortingDict


class _SSHConnection:
    """
    Helper class handling SFTP communication.

    If provided with a hostname, automatically initiates the SFTP session.

    :param hostname: The SSH host, defaults to :const:`None`.
    :type hostname: str, optional
    :param port: The port where the SSH host is listening, defaults to :const:`None`.
    :type port: int, optional
    :param username: The username on the target SSH host, defaults to :const:`None`.
    :type username: str, optional

    :ivar client: The SSH session handler.
    :vartype client: paramiko.client.SSHClient
    :ivar sftp_session: The SFTP session handler.
    :vartype sftp_session: paramiko.sftp_client.SFTPClient
    """

    client = None
    sftp_session = None

    def __init__(self, hostname: str = None, port: int = None, username: str = None):
        """Initialize object."""
        if hostname:
            self.set_session(hostname, port, username)

    def set_session(self, hostname: str, port: int = None, username: str = None):
        """
        Set up a SFTP session.

        :param str hostname: The SSH host.
        :param port: The port where the SSH host is listening, defaults to
          :const:`None`.
        :type port: int, optional
        :param username: The username on the target SSH host, defaults to :const:`None`.
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
        """Close the SFTP session."""
        if self.is_active():
            self.client.close()

    def mkdir_p(self, path: str):
        """
        Simulate the :command:`mkdir -p <path>` Unix command.

        It creates the directory and all its non-existing parents.

        :param str path: The path to a directory.
        """
        dirs = []

        while len(path) > 1:
            dirs.append(path)
            path = os.path.dirname(path)

        if len(path) == 1 and not path.startswith("/"):
            dirs.append(path)

        while dirs:
            path = dirs.pop()
            try:
                self.sftp_session.stat(path)
            except IOError:
                self.sftp_session.mkdir(path, mode=0o755)

    # def write_file(self, content: str, path: str):
    #     """
    #     Create or overwrite a file under `path` and store `content` in it.
    #
    #     It creates the parent directories if required.
    #
    #     :param str content: The file content.
    #     :param str path: Path to the new file.
    #     """
    #     self.mkdir_p(os.path.normpath(os.path.dirname(path)))
    #
    #     with self.sftp_session.open(path, "w") as sftp_file:
    #         sftp_file.write(content)

    def put_file(self, local_path, remote_path):
        """
        Copy the local file at `local_path` into `remote_path`.

        It creates the parent directories if required.

        :param str local_path: Path to the local file.
        :param str remote_path: Path to the remote file.
        """
        self.mkdir_p(os.path.normpath(os.path.dirname(remote_path)))
        self.sftp_session.put(local_path, remote_path)

    def is_active(self) -> bool:
        """Check whether the SSH session is active or not.

        :return: `True` if the SSH session is active, `False` otherwise.
        :rtype: bool
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


def _build_abs_schema_uri(rel_path: str, cb_schemas_base_url: str) -> str:
    """
    Form an absolute URI from a relative path.

    It takes the :code:`common.cb_schemas_base_url` property provided by the build
    configuration file.

    :param str rel_path: A path relative to :code:`build_params.root_build_dir`.
    :param str cb_schemas_base_url: The base URL pointing to the directory where the
      Cookbase Schemas are to be located.

    :return: An absolute URI intended to unambiguously refer to the given path.
    :rtype: str
    """
    base_url_splits = uritools.urisplit(cb_schemas_base_url)
    abs_path = base_url_splits.path or "/"

    return uritools.urijoin(cb_schemas_base_url, os.path.join(abs_path, rel_path))


def _build_rel_path(
    start_rel_path: str, target_rel_path: str, root_build_dir: str
) -> str:
    """
    Calculate the relative path from `start_rel_path` to `target_rel_path`.

    :param str start_rel_path: The start-point path.
    :param str target_rel_path: The target path.
    :param str root_build_dir: The absolute path to the directory where the built
      schemas are to be located.

    :return: A relative path from `start_rel_path` to `target_rel_path`.
    :rtype: str
    """
    base_path = uritools.urisplit(root_build_dir).path
    start_path = os.path.dirname(os.path.join(base_path, start_rel_path))
    target_path = os.path.join(base_path, target_rel_path)

    return os.path.relpath(target_path, start_path)


def render(template_path: str, substitutions: Dict[str, str]) -> str:
    """
    Generate a JSON Schema by applying substitutions on a template.

    :param str template_path: The path to the template file.
    :param substitutions: A dictionary including the substitutions to be performed on
      the template.
    :type substitutions: Dict[str, str]

    :return: The rendered JSON Schema.
    :rtype: str
    """
    with open(template_path) as file:
        template = string.Template(file.read())

    return template.substitute(substitutions)


def build_cb_common_definitions_schema(
    common_config: Dict[str, str], build_params: Dict[str, str]
) -> Tuple[str, str]:
    """
    Build the CB Common Definitions Schema.

    :param common_config: The :code:`common` configuration block.
    :type common_config: Dict[str, str]
    :param build_params: The :code:`build_params` configuration block.
    :type build_params: Dict[str, str]

    :return: A tuple having two elements, the rendered CB Common Definitions Schema as
      first element and the path where to be located as second element.
    :rtype: Tuple[str, str]
    """
    return (
        render(
            os.path.join(
                build_params["cb_schema_templates_dir"],
                "cb-common-definitions.template.json",
            ),
            {
                "json_schema_uri": common_config["json_schema_uri"],
                "cb_common_definitions_url": _build_abs_schema_uri(
                    common_config["defs_path"], common_config["cb_schemas_base_url"]
                ),
            },
        ),
        os.path.join(
            uritools.urisplit(build_params["root_build_dir"]).path,
            common_config["defs_path"],
        ),
    )


def build_cbr_schema(
    cbr_config: Dict[str, str],
    cbr_process_config: Dict[str, str],
    common_config: Dict[str, str],
    build_params: Dict[str, str],
) -> Tuple[Tuple[str, str]]:
    """
    Build the CBR Schema.

    :param cbr_config: The :code:`cbr` configuration block.
    :type cbr_config: Dict[str, str]
    :param cbr_process_config: The :code:`cbr_process` configuration block.
    :type cbr_process_config: Dict[str, str]
    :param common_config: The :code:`common` configuration block.
    :type common_config: Dict[str, str]
    :param build_params: The :code:`build_params` configuration block.
    :type build_params: Dict[str, str]

    :return: A tuple of tuples that represent the Cookbase Recipe Schema and all its
      subschemas. Each sub-tuple has two elements: a rendered JSON Schema representing
      either the Cookbase Recipe Schema itself or any of its subschemas as first
      element, and the path where the schema is to be located as second element.
    :rtype: Tuple[Tuple[str, str]]
    """

    def _render_subschema(subschema_name):
        return render(
            os.path.join(
                build_params["cb_schema_templates_dir"],
                f"cbr-{subschema_name}.template.json",
            ),
            {
                "json_schema_uri": common_config["json_schema_uri"],
                f"cbr_{subschema_name}_schema_url": _build_abs_schema_uri(
                    cbr_config[f"cbr_{subschema_name}_path"],
                    common_config["cb_schemas_base_url"],
                ),
                "common_defs_path": _build_rel_path(
                    cbr_config[f"cbr_{subschema_name}_path"],
                    common_config["defs_path"],
                    build_params["root_build_dir"],
                ),
            },
        )

    return (
        (
            render(
                os.path.join(
                    build_params["cb_schema_templates_dir"], "cbr.template.json"
                ),
                {
                    **{
                        key: _build_rel_path(
                            cbr_config["schema_path"],
                            value,
                            build_params["root_build_dir"],
                        )
                        for key, value in filter(
                            lambda item: item[0] != "schema_path", cbr_config.items()
                        )
                    },
                    **{
                        "json_schema_uri": common_config["json_schema_uri"],
                        "cbr_schema_url": _build_abs_schema_uri(
                            cbr_config["schema_path"],
                            common_config["cb_schemas_base_url"],
                        ),
                        "common_defs_path": _build_rel_path(
                            cbr_config["schema_path"],
                            common_config["defs_path"],
                            build_params["root_build_dir"],
                        ),
                    },
                },
            ),
            os.path.join(
                uritools.urisplit(build_params["root_build_dir"]).path,
                cbr_config["schema_path"],
            ),
        ),
        (
            _render_subschema("info"),
            os.path.join(
                uritools.urisplit(build_params["root_build_dir"]).path,
                cbr_config["cbr_info_path"],
            ),
        ),
        (
            _render_subschema("yield"),
            os.path.join(
                uritools.urisplit(build_params["root_build_dir"]).path,
                cbr_config["cbr_yield_path"],
            ),
        ),
        (
            _render_subschema("ingredient"),
            os.path.join(
                uritools.urisplit(build_params["root_build_dir"]).path,
                cbr_config["cbr_ingredient_path"],
            ),
        ),
        (
            _render_subschema("appliance"),
            os.path.join(
                uritools.urisplit(build_params["root_build_dir"]).path,
                cbr_config["cbr_appliance_path"],
            ),
        ),
        *build_cbr_process_schema(
            cbr_config["cbr_process_path"],
            cbr_process_config,
            common_config,
            build_params,
        ),
    )


def build_cbi_schema(
    cbi_schema_path: str, common_config: Dict[str, str], build_params: Dict[str, str]
) -> Tuple[str, str]:
    """
    Build the CBI Schema.

    :param str cbi_schema_path: The relative path to the Cookbase Ingredient Schema.
    :param common_config: The :code:`common` configuration block.
    :type common_config: Dict[str, str]
    :param build_params: The :code:`build_params` configuration block.
    :type build_params: Dict[str, str]

    :return: A tuple having two elements, the rendered Cookbase Ingredient Schema as
      first element and the path where to be located as second element.
    :rtype: Tuple[str, str]
    """
    return (
        render(
            os.path.join(build_params["cb_schema_templates_dir"], "cbi.template.json"),
            {
                "json_schema_uri": common_config["json_schema_uri"],
                "cbi_schema_url": _build_abs_schema_uri(
                    cbi_schema_path, common_config["cb_schemas_base_url"],
                ),
                "common_defs_path": _build_rel_path(
                    cbi_schema_path,
                    common_config["defs_path"],
                    build_params["root_build_dir"],
                ),
            },
        ),
        os.path.join(
            uritools.urisplit(build_params["root_build_dir"]).path, cbi_schema_path
        ),
    )


def build_cba_schema(
    cba_schema_path: str, common_config: Dict[str, str], build_params: Dict[str, str]
) -> Tuple[str, str]:
    """
    Build the CBA Schema.

    :param str cba_schema_path: The relative path to the Cookbase Appliance Schema.
    :param common_config: The :code:`common` configuration block.
    :type common_config: Dict[str, str]
    :param build_params: The :code:`build_params` configuration block.
    :type build_params: Dict[str, str]

    :return: A tuple having two elements, the rendered Cookbase Appliance Schema as
      first element and the path where to be located as second element.
    :rtype: Tuple[str, str]
    """
    return (
        render(
            os.path.join(build_params["cb_schema_templates_dir"], "cba.template.json"),
            {
                "json_schema_uri": common_config["json_schema_uri"],
                "cba_schema_url": _build_abs_schema_uri(
                    cba_schema_path, common_config["cb_schemas_base_url"],
                ),
                "common_defs_path": _build_rel_path(
                    cba_schema_path,
                    common_config["defs_path"],
                    build_params["root_build_dir"],
                ),
            },
        ),
        os.path.join(
            uritools.urisplit(build_params["root_build_dir"]).path, cba_schema_path
        ),
    )


def build_cbp_schema(
    cbp_schema_path: str, common_config: Dict[str, str], build_params: Dict[str, str]
) -> Tuple[str, str]:
    """
    Build the CBP Schema.

    :param str cbp_schema_path: The relative path to the Cookbase Process Schema.
    :param common_config: The :code:`common` configuration block.
    :type common_config: Dict[str, str]
    :param build_params: The :code:`build_params` configuration block.
    :type build_params: Dict[str, str]

    :return: A tuple having two elements, the rendered Cookbase Process Schema as first
      element and the path where to be located as second element.
    :rtype: Tuple[str, str]
    """
    return (
        render(
            os.path.join(build_params["cb_schema_templates_dir"], "cbp.template.json"),
            {
                "json_schema_uri": common_config["json_schema_uri"],
                "cbp_schema_url": _build_abs_schema_uri(
                    cbp_schema_path, common_config["cb_schemas_base_url"],
                ),
                "common_defs_path": _build_rel_path(
                    cbp_schema_path,
                    common_config["defs_path"],
                    build_params["root_build_dir"],
                ),
            },
        ),
        os.path.join(
            uritools.urisplit(build_params["root_build_dir"]).path, cbp_schema_path
        ),
    )


def build_caf_schema(
    caf_schema_path: str, common_config: Dict[str, str], build_params: Dict[str, str]
) -> Tuple[str, str]:
    """
    Build the CAF Schema.

    :param str caf_schema_path: The relative path to the Cookbase Appliance Function
      Schema.
    :param common_config: The :code:`common` configuration block.
    :type common_config: Dict[str, str]
    :param build_params: The :code:`build_params` configuration block.
    :type build_params: Dict[str, str]

    :return: A tuple having two elements, the rendered Cookbase Appliance Function
      Schema as first element and the path where to be located as second element.
    :rtype: Tuple[str, str]
    """
    return (
        render(
            os.path.join(build_params["cb_schema_templates_dir"], "caf.template.json"),
            {
                "json_schema_uri": common_config["json_schema_uri"],
                "caf_schema_url": _build_abs_schema_uri(
                    caf_schema_path, common_config["cb_schemas_base_url"],
                ),
                "common_defs_path": _build_rel_path(
                    caf_schema_path,
                    common_config["defs_path"],
                    build_params["root_build_dir"],
                ),
            },
        ),
        os.path.join(
            uritools.urisplit(build_params["root_build_dir"]).path, caf_schema_path
        ),
    )


def build_cbr_process_schema(
    cbr_process_path: str,
    cbr_process_config: Dict[str, str],
    common_config: Dict[str, str],
    build_params: Dict[str, str],
) -> Tuple[Tuple[str, str]]:
    """
    Build the CBR Process Schema.

    :param str cbr_process_path: The relative path to the CBR Process Main Schema.
    :param cbr_process_config: The :code:`cbr_process` configuration block.
    :type cbr_process_config: Dict[str, str]
    :param common_config: The :code:`common` configuration block.
    :type common_config: Dict[str, str]
    :param build_params: The :code:`build_params` configuration block.
    :type build_params: Dict[str, str]

    :return: A tuple of tuples that represent the CBR Process Main Schema and its
      subschemas. Each sub-tuple has two elements: a rendered JSON Schema representing
      either the CBR Process Main Schema itself or any of its subschemas as first
      element, and the path where the schema is to be located as second element.
    :rtype: Tuple[Tuple[str, str]]
    """
    cbr_process_collection = generate_cbr_process_collection(
        cbr_process_config, common_config, build_params
    )
    return (
        build_cbr_process_definitions_schema(
            cbr_process_config["defs_path"], common_config, build_params
        ),
        *cbr_process_collection,
        generate_cbr_process_main_schema(
            cbr_process_path,
            cbr_process_config["cbr_process_collection_dir"],
            common_config,
            build_params,
            tuple(os.path.basename(path) for _, path in cbr_process_collection),
        ),
    )


def build_cbr_process_definitions_schema(
    cbr_defs_path: str, common_config: Dict[str, str], build_params: Dict[str, str],
) -> Tuple[str, str]:
    """
    Build the CBR Process Definitions Schema.

    :param str cbr_defs_path: The relative path to the CBR Process Definitions Schema.
    :param common_config: The :code:`common` configuration block.
    :type common_config: Dict[str, str]
    :param build_params: The :code:`build_params` configuration block.
    :type build_params: Dict[str, str]

    :return: A tuple having two elements, the rendered CBR Process Definitions Schema as
      first element and the path where to be located as second element.
    :rtype: Tuple[str, str]
    """
    return (
        render(
            os.path.join(
                build_params["cb_schema_templates_dir"],
                "cbr-process-definitions.template.json",
            ),
            {
                "json_schema_uri": common_config["json_schema_uri"],
                "cbr_process_definitions_url": _build_abs_schema_uri(
                    cbr_defs_path, common_config["cb_schemas_base_url"],
                ),
            },
        ),
        os.path.join(
            uritools.urisplit(build_params["root_build_dir"]).path, cbr_defs_path
        ),
    )


def generate_cbr_process_collection(
    cbr_process_config: Dict[str, str],
    common_config: Dict[str, str],
    build_params: Dict[str, str],
) -> Tuple[Tuple[str, str]]:
    r"""
    Build the collection of CBR Process Schemas.

    Generates and writes into files the CBR Process Schemas from a collection of CBP
    files, which are under the directory specified by the :code:`cbr_process.cbp_dir`
    property from the build configuration file. The routes to the JSON Schema
    definitions of the different :code:`type`\ s referred by the CBP documents are
    detailed in the configuration file under the path given by the
    :code:`cbr_process.types_path` property.

    :param cbr_process_config: The :code:`cbr_process` configuration block.
    :type cbr_process_config: Dict[str, str]
    :param common_config: The :code:`common` configuration block.
    :type common_config: Dict[str, str]
    :param build_params: The :code:`build_params` configuration block.
    :type build_params: Dict[str, str]

    :return: A tuple of tuples that represent the collection of CBR Process Schemas.
      Each sub-tuple has two elements: a rendered JSON Schema representing either the
      CBR Process Schema as first element, and the path where the schema is to
      be located as second element.
    :rtype: Tuple[Tuple[str, str]]
    """

    def build_ref(type_entry):
        if type_entry["ns"] == "common":
            defs_path = common_config["defs_path"]
        elif type_entry["ns"] == "cbr_process":
            defs_path = cbr_process_config["defs_path"]

        return uritools.urijoin(
            _build_rel_path(
                os.path.join(cbr_process_config["cbr_process_collection_dir"], "dummy"),
                defs_path,
                build_params["root_build_dir"],
            ),
            f"#{type_entry['def']}",
        )

    with open(cbr_process_config["types_path"]) as file:
        types = YAML().load(file)

    defs = {i: build_ref(types[i]) for i in types.keys()}

    cbp_filenames = tuple(
        filter(
            lambda filename: os.path.splitext(filename)[1] == ".cbp",
            os.listdir(cbr_process_config["cbp_dir"]),
        )
    )

    cbr_processes = {}

    for cbp_filename in cbp_filenames:
        with open(os.path.join(cbr_process_config["cbp_dir"], cbp_filename)) as file:
            cbp = json.load(file, object_pairs_hook=OrderedDict)

        if cbp["data"]["processType"] == "generic":
            cbr_processes[
                os.path.join(
                    cbr_process_config["cbr_process_collection_dir"],
                    cbp_filename.rsplit("-", 1)[0] + ".json",
                )
            ] = cbp

    return tuple(
        (
            generate_cbr_process_collection_item(
                cbp,
                defs,
                common_config["json_schema_uri"],
                _build_abs_schema_uri(
                    schema_path, common_config["cb_schemas_base_url"]
                ),
            ),
            os.path.join(
                uritools.urisplit(build_params["root_build_dir"]).path, schema_path
            ),
        )
        for schema_path, cbp in cbr_processes.items()
    )


def generate_cbr_process_collection_item(
    cbp: Dict[str, Any], defs: Dict[str, str], json_schema_uri: str, cbr_schema_uri: str
) -> str:
    """
    Build a CBR Process Schema from a CBP document.

    If `schema_filename` is set to :const:`None` (the default), the output file name
    will be assumed to be the first English name given in the CBP's :code:`name`
    property, lowercased, substituted spaces by underscores :const:`_`, and appended the
    :code:`.json` extension.

    :param cbp: The dictionary representing the content of a CBP document.
    :type cbp: dict[str, Any]
    :param defs: A dictionary mapping the CBP.
      :code:`data.schema.foodstuffKeywords.*.type` properties to the location of its
      definition
    :type defs: dict[str, str]
    :param str json_schema_uri: The URI identifying the followed JSON Schema
      specification.
    :param str cbr_schema_uri: The absolute URI referring to the CBR Process Schema.

    :return: The CBR Process Schema.
    :rtype: str

    :raises ValueError: The processed CBP does not have :code:`"generic"` as
      :code:`data.processType`.
    """
    # It assumes a valid CBP
    if cbp["data"]["processType"] != "generic":
        raise ValueError('The processed CBP has wrong "processType".')

    # Get CBP name
    process_name = cbp["name"]["en"]

    if isinstance(process_name, list):
        process_name = process_name[0]

    schema = {}
    schema["$schema"] = json_schema_uri
    schema["$id"] = cbr_schema_uri
    schema["title"] = f'Cookbase Recipe Process "{process_name}"'
    schema[
        "description"
    ] = f'Schema defining the format of the CBR "{process_name}" Process.'
    schema["type"] = "object"
    schema["additionalProperties"] = False
    schema["required"] = ["name", "cbpId"]
    schema["properties"] = {
        "name": {"$ref": defs["name"]},
        "cbpId": {"const": cbp["id"]},
    }

    # Generate parameters property
    parameters_is_required = False

    if cbp["data"]["schema"].get("parameters"):
        schema["properties"]["parameters"] = {
            "type": "object",
            "additionalProperties": False,
        }

        required_params = []
        properties_params = {}

        for param_key, param_value in cbp["data"]["schema"]["parameters"].items():
            if param_key == "endConditions":
                properties_params["endConditions"] = {
                    "type": "object",
                    "additionalProperties": False,
                }

                required_end_condition = []
                properties_end_condition = {}

                for end_condition_key, end_condition_value in param_value.items():
                    if end_condition_value["required"]:
                        parameters_is_required = False
                        required_end_condition.append(end_condition_key)

                    properties_end_condition[end_condition_key] = {
                        "$ref": defs[end_condition_key]
                    }

                if required_end_condition:
                    properties_params["endConditions"][
                        "required"
                    ] = required_end_condition

                properties_params["endConditions"][
                    "properties"
                ] = properties_end_condition

            else:
                if param_value["required"]:
                    parameters_is_required = False
                    required_params.append(param_key)

                properties_params[param_key] = {"$ref": defs[param_key]}

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
    for foodstuff_key, foodstuff_value in cbp["data"]["schema"][
        "foodstuffKeywords"
    ].items():
        if foodstuff_value["required"]:
            schema["required"].append(foodstuff_key)

        schema["properties"][foodstuff_key] = {"$ref": defs[foodstuff_value["type"]]}

    # Generate appliances property
    schema["required"].append("appliances")
    schema["properties"]["appliances"] = {"$ref": defs["appliances"]}

    if cbp["data"]["schema"].get("flags"):
        for foodstuff_key in cbp["data"]["schema"]["flags"]:
            schema["required"].append(foodstuff_key)
            schema["properties"][foodstuff_key] = {"const": True}

    schema["properties"]["notes"] = {"$ref": defs["notes"]}

    return json.dumps(schema, indent=2)


def generate_cbr_process_main_schema(
    cbr_process_path: str,
    cbr_process_collection_dir: str,
    common_config: Dict[str, str],
    build_params: Dict[str, str],
    cbr_process_collection_filenames: Tuple[str],
) -> Tuple[str, str]:
    """
    Build the CBR Process Main Schema from a collection of CBR Process Schemas.

    :param str cbr_process_path: The relative path to the CBR Process Main Schema.
    :param str cbr_process_collection_dir: The relative path to the directory containing
      the collection of CBR Process Schemas.
    :param common_config: The :code:`common` configuration block.
    :type common_config: Dict[str, str]
    :param build_params: The :code:`build_params` configuration block.
    :type build_params: Dict[str, str]
    :param cbr_process_collection_filenames: The names of all files containing the
      collection of CBR Process Schemas.
    :type cbr_process_collection_filenames: Tuple[str]

    :return: A tuple having two elements, the rendered CBR Process Main Schema as first
      element and the path where to be located as second element.
    :rtype: Tuple[str, str]
    """
    schema = {}
    schema["$schema"] = common_config["json_schema_uri"]
    schema["$id"] = _build_abs_schema_uri(
        cbr_process_path, common_config["cb_schemas_base_url"]
    )
    schema["title"] = "Cookbase Recipe Process"
    schema["description"] = (
        "Schema defining the format of the Cookbase Recipe Process. Visit "
        "https://cookbase.readthedocs.io/en/latest/cbdm.html#cbr-preparation to read "
        "the documentation."
    )
    schema["oneOf"] = []

    for cbr_process_filename in cbr_process_collection_filenames:
        bisect.insort(
            schema["oneOf"],
            _SortingDict(
                {
                    "$ref": _build_rel_path(
                        cbr_process_path,
                        os.path.join(cbr_process_collection_dir, cbr_process_filename),
                        build_params["root_build_dir"],
                    )
                }
            ),
        )

    return (
        json.dumps(schema, indent=2),
        os.path.join(
            uritools.urisplit(build_params["root_build_dir"]).path, cbr_process_path
        ),
    )


def build_config(custom_config_path: str = None):
    """
    Generate the builder configuration.

    If a custom build configuration file `custom_config_path` is not provided, the
    default build configuration is loaded; if provided, all provided parameters will
    override the default configuration.

    :param custom_config_path: Path to the custom build configuration file, defaults to
      :const:`None`.
    :type config_path: str, optional

    :raises ConfigError: The custom configuration file has a wrong format.
    """

    def _build_config(default_config, custom_config):
        def process_config_value(key, default_value, custom_value):
            if isinstance(default_value, dict):
                return _build_config(default_value, custom_value)

            if key == "root_build_dir":
                value = custom_value or default_value

                return value if uritools.isabsuri(value) else os.path.abspath(value)

            if key in ("cbp_dir", "cb_schema_templates_dir", "types_path"):
                if custom_value:
                    return os.path.abspath(custom_value)

                return os.path.normpath(
                    os.path.join(os.path.dirname(__file__), default_value)
                )

            return custom_value or default_value

        if custom_config is not None and not isinstance(custom_config, Mapping):
            raise ConfigError("malformed custom configuration file")

        return {
            k: process_config_value(k, v, custom_config.get(k, {}))
            for k, v in default_config.items()
        }

    with open(os.path.join(os.path.dirname(__file__), "build-config.yaml")) as file:
        default_config = YAML().load(file)

    if custom_config_path:
        with open(custom_config_path) as file:
            custom_config = YAML().load(file)
    else:
        custom_config = {}

    return _build_config(default_config, custom_config)


class ConfigError(Exception):
    """Class defining errors thrown when a configuration parsing problem arises."""

    def __init__(self, message: str):
        """
        Initialize exception.

        :param str message: The specific error message.
        """
        super().__init__(f"Error parsing configuration due to {message}.")


def main(args: Namespace):
    """
    Run the module with the provided configuration.

    In case that the :code:`build_params.root_build_dir` configuration property
    consists of a SSH or SFTP URI, a SFTP session with the target host is opened in
    order to store the files remotely.

    .. warning::
       This function generates output files and may overwrite stored data.

    :param args: The passed arguments including the `config_path` attribute which holds
      the path to the custom configuration file.
    :type args: argparse.Namespace

    :raises ValueError: The URI under the :code:`build_params.root_build_dir`
      configuration property is neither a SSH/SFTP URI nor a filesystem path.
    """
    print(args.config_path)
    config = build_config(args.config_path)
    build_dir_splits = uritools.urisplit(config["build_params"]["root_build_dir"])

    ssh = (
        _SSHConnection(
            str(build_dir_splits.gethost()),
            build_dir_splits.getport(22),
            build_dir_splits.getuserinfo(),
        )
        if build_dir_splits.getscheme() == "ssh"
        or build_dir_splits.getscheme() == "sftp"
        else None
    )

    if build_dir_splits.getscheme("file") not in ("ssh", "sftp", "file"):
        raise ValueError(
            "The URI given to the root_build_dir configuration is neither a SSH URI nor"
            " a filesystem path."
        )

    for schema, path in (
        build_cb_common_definitions_schema(config["common"], config["build_params"]),
        *build_cbr_schema(
            config["cbr"],
            config["cbr_process"],
            config["common"],
            config["build_params"],
        ),
        build_cbi_schema(
            config["cbi"]["schema_path"], config["common"], config["build_params"]
        ),
        build_cba_schema(
            config["cba"]["schema_path"], config["common"], config["build_params"]
        ),
        build_cbp_schema(
            config["cbp"]["schema_path"], config["common"], config["build_params"]
        ),
        build_caf_schema(
            config["caf"]["schema_path"], config["common"], config["build_params"]
        ),
    ):
        if ssh:
            with tempfile.NamedTemporaryFile() as temp_file:
                temp_file.write(schema.encode())
                temp_file.seek(0)
                ssh.put_file(temp_file.name, path)
        else:
            os.makedirs(os.path.dirname(path), mode=0o755, exist_ok=True)

            with open(path, "w") as file:
                file.write(schema)

    if ssh:
        ssh.close_session()
