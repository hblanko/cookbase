from typing import Any, Dict, List, Union

import requests
import uritools
from jsonschema.validators import RefResolver


class SchemaRetriever:
    def __init__(self, url: str):
        self._resolver = RefResolver.from_schema(requests.get(url).json())

    @staticmethod
    def retrieve(url: str) -> Dict[str, Any]:
        """Retrieves a complete :doc:`Cookbase Schema (CBSchema)<cbdm>`.

        This function assumes JSON Schema validity.

        :param str url: An absolute URI indicating the location of the `CBSchema <cbdm>`
          to be retrieved
        :return: A dictionary containing the requested `CBSchema <cbdm>`
        :rtype: dict[str, Any]
        """
        retriever = SchemaRetriever(url)
        return retriever._resolve_schema(url)

    def _resolve_schema(self, url: str) -> Dict[str, Any]:
        """Resolves a `CBSchema <cbdm>` object recursively.

        This function assumes JSON Schema validity.

        :param str url: An absolute URI indicating the location of the `CBSchema <cbdm>`
          object to retrieve
        :return: A dictionary containing the requested `CBSchema <cbdm>` object
        :rtype: dict[str, Any]
        """
        schema = self._resolver.resolve_from_url(url)

        def recursive_traversal(
            schema_object: Union[Dict[str, Any], List[Any]]
        ) -> Dict[str, Any]:
            retrieved_object = None

            if isinstance(schema_object, dict):
                for k, v in schema_object.items():
                    if isinstance(v, dict) or isinstance(v, list):
                        recursive_traversal(v)
                    elif k == "$ref":
                        # Processes case
                        if v.startswith("processes/"):
                            pass
                        else:
                            if not uritools.urisplit(v).gethost():
                                v = uritools.urijoin(url, v)
                            retrieved_object = self._resolve_schema(v)

                if retrieved_object is not None:
                    schema_object.update(retrieved_object)
                    del schema_object["$ref"]
            if isinstance(schema_object, list):
                for i in schema_object:
                    if isinstance(i, dict) or isinstance(i, list):
                        recursive_traversal(i)

        recursive_traversal(schema)
        return schema


if __name__ == "__main__":
    from pprint import pprint
    import time

    t = time.time()
    s = SchemaRetriever.retrieve("http://www.landarltracker.com/schemas/cba/cba.json")
    print(time.time() - t)

    if "$defs" in s:
        del s["$defs"]

    if "examples" in s:
        del s["examples"]

    pprint(s)
