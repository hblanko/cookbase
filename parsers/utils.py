import json
import os
from typing import Any, Dict, Hashable, List, Tuple


def check_for_duplicate_keys(
        ordered_pairs: List[Tuple[Hashable, Any]]) -> Dict:
    """Checks for duplicates on the keys of a JSON object

    The function is defined to be used as the `object_pairs_hook` argument of a :meth:`json.load` method.
    :param ordered_pairs: A list of key-value pairs representing all the content of a JSON object
    :type ordered_pairs: list[tuple[Hashable, Any]]
    :raises: :class:`ValueError`: There is at least one duplicate key in the JSON object.
    """
    dict_out = dict()
    for key, val in ordered_pairs:
        if key in dict_out:
            raise ValueError("duplicate key: " + key)
        else:
            dict_out[key] = val
    return dict_out


def parse_json_recipe(path: str) -> Dict:
    """Parses the JSON recipe handling duplicate keys

    :param str path: The path to the file containing the recipe data
    :return: A dict containing the JSON document
    :rtype: dict[str, Any]

    :raises: :class:`OSError`: The file could not be opened.
    :raises: :class:`JSONDecodeError`: The JSON document could not be decoded.
    :raises: :class:`ValueError`: There is at least one duplicate key in the JSON document.
    """
    with open(path) as f:
        return json.load(f, object_pairs_hook=check_for_duplicate_keys)


def populate_collection(collection_dir: str, object_type: str) -> None:
    """Bulk inserts Cookbase objects into collections

    :param str collection_dir: The local path to the directory containing the objects to insert
    :param str object_type: The type of object to insert into collection
    """
    from cookbase.db.utils import underscore_id
    from cookbase.db.handler import db_handler

    db_handler._default_db[collection_dir].delete_many({})

    docs = list()

    for e in os.scandir(collection_dir):
        if e.path.endswith("." + object_type):
            with open(e.path) as f:
                docs.append(json.load(f, object_hook=underscore_id))

    db_handler._default_db[collection_dir].insert_many(docs)
