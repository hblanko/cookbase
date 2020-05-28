import json
import os
from typing import Any, Dict, Hashable, List, Tuple


def check_for_duplicate_keys(ordered_pairs: List[Tuple[Hashable, Any]]) -> Dict:
    """Checks for duplicates on the keys of a JSON object.

    The function is defined to be used as the :code:`object_pairs_hook` argument of a
    :meth:`json.load` method.

    :param ordered_pairs: A list of key-value pairs representing all the content of a
      JSON object
    :type ordered_pairs: list[tuple[Hashable, Any]]
    :return: A dictionary containing the JSON document
    :rtype: dict[str, Any]

    :raises: :class:`ValueError`: There is at least one duplicate key in the JSON
      object.
    """
    dict_out = {}
    for key, val in ordered_pairs:
        if key in dict_out:
            raise ValueError(f"duplicate key: {key}")
        else:
            dict_out[key] = val
    return dict_out


def parse_cbr(path: str) -> Dict[str, Any]:
    """Parses a :ref:`Cookbase Recipe (CBR) <cbr>`.

    :param str path: The path to the :ref:`CBR <cbr>` document
    :return: A dictionary containing the parsed :ref:`CBR <cbr>`
    :rtype: dict[str, Any]
    """
    with open(path) as f:
        return json.load(f, object_pairs_hook=check_for_duplicate_keys)


def populate_collection(collection_dir: str, object_type: str) -> None:
    """Bulk inserts :doc:`CBDM <cbdm>` objects into collections.

    :param str collection_dir: The local path to the directory containing the objects to
      insert
    :param str object_type: The type of object to insert into collection
    """
    from cookbase.db.utils import underscore_id
    from cookbase.db.handler import db_handler

    db_handler._default_db[collection_dir].delete_many({})

    docs = []

    for e in os.scandir(collection_dir):
        if e.path.endswith(f".{object_type}"):
            with open(e.path) as f:
                docs.append(json.load(f, object_hook=underscore_id))

    db_handler._default_db[collection_dir].insert_many(docs)
