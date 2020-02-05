import requests
from typing import Any, Dict, Union

import jsonschema

from cookbase.db.handler import db_handler
from cookbase.graph.recipegraph import RecipeGraph
from cookbase.validation import rules
from cookbase.validation.globals import Definitions
from cookbase.validation.logger import logger


class Validator():
    """Class performing validation and graph construction of recipes in Cookbase Recipe Format (CBR).

    :ivar schema: The JSON Schema defining the Cookbase Recipe Format
    :vartype schema: dict[str, Any]
    :ivar graph: An instance of :class:`cookbase.graph.recipegraph.RecipeGraph` storing the CBR-Graph information
    :vartype graph: cookbase.graph.recipegraph.RecipeGraph
    """
    graph = RecipeGraph()

    def __init__(self,
                 schema_url: str = Definitions.cbr_schema_url):
        """Constructor method

        It performs an HTTP request to the given url to get the JSON Schema

        :param schema_url: A url to the CBR JSON Schema
        """
        r = requests.get(schema_url)
        r.raise_for_status()
        if len(r.content) == 0:
            raise Exception(
                "the HTTP response from requesting JSON Schema is empty")
        self.schema = r.json()

    def _store(self, data: Dict[str, Any]) -> Union[int, bool]:
        """Stores CBR and its CBR-Graph into database

        The data is stored using the :data:`cookbase.db.handler.db_handler` object.

        :param data: The dict containing the validated CBR
        :type data: dict[str, Any]
        :return: If CBR and CBR-Graph insertion was successful returns the id of the stored object,
        otherwise returns `False`
        :rtype: int or bool
        """
        return db_handler.insert_cbr(data, self.graph.get_serializable_graph())

    def apply_validation_rules(self, data: Dict[str, Any]) -> Dict[str, bool]:
        """Validates CBR against a set of definition rules

        Validation rules defined in :mod:`cookbase.validation.rules` are applied sequentially to ensure that the recipe document satisfies
        the CBR definition.

        :param data: The JSON document representing the recipe to be validated
        :type data: dict[str, Any]
        """
        result = dict()
        result["cbis_are_valid"] = rules.Semantics.cbis_are_valid(
            data["ingredients"])
        result["foodstuff_and_appliance_references_are_consistent"] = rules.Semantics.foodstuff_and_appliance_references_are_consistent(
            data["ingredients"], data["appliances"], data["preparation"])
        result["cbps_and_cbas_are_valid_and_processes_requirements_met"] = rules.Semantics.cbps_and_cbas_are_valid_and_processes_requirements_met(
            data["appliances"], data["preparation"])
        self.graph.build_graph(data)
        result["ingredients_used_only_once"] = rules.Graph.ingredients_used_only_once(
            self.graph)
        result["single_final_process"] = rules.Graph.single_final_process(
            self.graph)
        result["appliances_not_in_conflict"] = rules.Graph.appliances_not_in_conflict(
            self.graph)
        return result

    def validate(self,
                 data: Dict[str, Any], store: bool = False) -> Dict[str, Union[bool, int]]:
        """Performs validation of a CBR and builds the CBR-Graph

        The validation process is implemented in two stages: firstly, a JSON Schema validation is performed,
        and, secondly, validating rules are sequentially applied to ensure that the recipe document satisfies
        the CBR definition.

        :param data: The JSON document representing the recipe to be validated
        :type data: dict[str, Any]
        :param bool store: A flag indicating whether the validated CBR and CBR-Graph should be stored in database
        """
        jsonschema.validate(data, self.schema)
        self.graph.clear()
        result = self.apply_validation_rules(data)
        if store:
            r = self._store(data)
            if r:
                result["inserted_id"] = r
            else:
                logger.error("Storing CBR and/or CBR-Graph unsuccessful")
        return result


if __name__ == '__main__':
    import time
    from cookbase.parsers import utils

    logger.info("Start logging")
#     recipe = db_handler.get_cbr({"info.name": "Pizza mozzarella"})
    recipe_path = "../resources/cbr/pizzaMozzarella.json"
    recipe = utils.parse_json_recipe(recipe_path)
    t1 = time.time()
    result = Validator().validate(recipe, store=True)
    if "inserted_id" in result:
        logger.info("CBR and CBR-Graph inserted with ID " +
                    str(result["inserted_id"]))
    t2 = time.time()
    logger.info("Recipe validation: " + str(int((t2 - t1) * 1000)) + " ms")
    logger.info(result)
