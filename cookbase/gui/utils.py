import requests
from typing import Any, Dict, List, Union
from urllib import parse

from jsonschema.validators import RefResolver


class SchemaRetriever():

    def __init__(self, url):
        self._resolver = RefResolver.from_schema(requests.get(url).json())

    @staticmethod
    def retrieve(url: str) -> Dict[str, Any]:
        '''Retrieves a complete Cookbase Format Schema

        This function assumes JSON Schema validity.

        :param str url: An absolute URI indicating the location of the JSON Schema object to retrieve
        :return: A dictionary containing the requested JSON Schema object
        :rtype: dict[str, Any]
        '''
        retriever = SchemaRetriever(url)
        return retriever._resolve_schema(url)

    def _resolve_schema(self, url: str) -> Dict[str, Any]:
        '''Resolves a JSON Schema object recursively

        This function assumes JSON Schema validity.

        :param str url: An absolute URI indicating the location of the JSON Schema object to retrieve
        :return: A dictionary containing the requested JSON Schema object
        :rtype: dict[str, Any]
        '''
        schema = self._resolver.resolve_from_url(url)

        def recursive_traversal(
                schema_object: Union[Dict[str, Any], List[Any]]) -> Dict[str, Any]:
            retrieved_object = None

            if isinstance(schema_object, dict):
                for k, v in schema_object.items():
                    if isinstance(v, dict) or isinstance(v, list):
                        recursive_traversal(v)
                    elif k == '$ref':
                        # Processes case
                        if v.startswith('processes/'):
                            pass
                        else:
                            if not bool(parse.urlparse(v).netloc):
                                v = parse.urljoin(url, v)
                            retrieved_object = self._resolve_schema(v)

                if retrieved_object is not None:
                    schema_object.update(retrieved_object)
                    del schema_object['$ref']
            if isinstance(schema_object, list):
                for i in schema_object:
                    if isinstance(i, dict) or isinstance(i, list):
                        recursive_traversal(i)

        recursive_traversal(schema)
        return schema


if __name__ == '__main__':
    from pprint import pprint
    import time
#     import timeit
#     print(timeit.timeit(
#         "SchemaRetriever.retrieve('http://www.landarltracker.com/schemas/cbr.json')",
#         "from cookbase.gui.utils import SchemaRetriever",
#         number=2))
    t = time.time()
    s = SchemaRetriever.retrieve(
        'http://www.landarltracker.com/schemas/cba.json')
    print(time.time() - t)
    if "definitions" in s:
        del s["definitions"]
    if "examples" in s:
        del s["examples"]
    pprint(s)
