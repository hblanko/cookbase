from typing import Any, Dict, Union

import jsonschema
import requests

from cookbase.db.handler import db_handler
from cookbase.graph.recipegraph import RecipeGraph
from cookbase.validation import rules
from cookbase.validation.globals import Definitions
from cookbase.validation.logger import logger


class Validator():
    '''A class that performs validation and :doc:`Cookbase Recipe Graph (CBRGraph)
    <cbrg>` construction of recipes in :ref:`Cookbase Recipe format (CBR) <cbr>`.

    :param schema_url: A URL to where the :ref:`CBR <cbr>` Schema is to be retrieved,
      defaults to :attr:`cookbase.validation.globals.Definitions.cbr_schema_url`
    :type schema_url: str, optional

    :raises Exception: The HTTP response from requesting the :ref:`CBR <cbr>` Schema is
      empty

    :ivar schema: The :ref:`CBR <cbr>` schema
    :vartype schema: dict[str, Any]
    :ivar graph: An instance of :class:`cookbase.graph.recipegraph.RecipeGraph` storing
      the :doc:`CBRGraph <cbrg>` data
    :vartype graph: cookbase.graph.recipegraph.RecipeGraph

    '''
    graph = RecipeGraph()

    def __init__(self, schema_url: str = Definitions.cbr_schema_url):
        '''Constructor method.'''
        r = requests.get(schema_url)
        r.raise_for_status()

        if len(r.content) == 0:
            raise Exception('the HTTP response from requesting JSON Schema is empty')

        self.schema = r.json()

    def _store(self, data: Dict[str, Any]) -> Union[int, bool]:
        '''Stores a :ref:`CBR <cbr>` and its :doc:`CBRGraph <cbrg>` into database.

        The data is stored using the :data:`cookbase.db.handler.db_handler` object.

        :param data: The dictionary containing the validated :ref:`CBR <cbr>`
        :type data: dict[str, Any]
        :return: If :ref:`CBR <cbr>` and :doc:`CBRGraph <cbrg>` insertion was successful
          returns the identifier of the stored object, returns :const:`False` otherwise
        :rtype: int or bool
        '''
        return db_handler.insert_cbr(data, self.graph.get_serializable_graph())

    def apply_validation_rules(self, data: Dict[str, Any]) -> Dict[str, bool]:
        '''Validates a :ref:`CBR <cbr>` against the set of definition rules.

        Validation rules defined in :mod:`cookbase.validation.rules` are applied
        sequentially to ensure that the recipe document satisfies the :ref:`CBR <cbr>`
        definition.

        :param data: The :ref:`CBR <cbr>` to be validated
        :type data: dict[str, Any]
        :return: A dictionary indicating the results of the validation process
        :rtype: dict[str, bool]
        '''
        result = {}
        result['ingredients_are_valid'] = \
            rules.Semantics.ingredients_are_valid(data['ingredients'])
        result['foodstuff_and_appliance_references_are_consistent'] = \
            rules.Semantics.foodstuff_and_appliance_references_are_consistent(
            data['ingredients'], data['appliances'], data['preparation'])
        result['processes_and_appliances_are_valid_and_processes_requirements_met'] = \
            rules.Semantics.
        processes_and_appliances_are_valid_and_processes_requirements_met(
            data['appliances'], data['preparation'])
        self.graph.build_graph(data)
        result['ingredients_used_only_once'] = rules.Graph.ingredients_used_only_once(
            self.graph)
        result['single_final_process'] = rules.Graph.single_final_process(self.graph)
        result['appliances_not_in_conflict'] = rules.Graph.appliances_not_in_conflict(
            self.graph)
        return result

    def validate(self,
                 data: Dict[str, Any],
                 store: bool = False) -> Dict[str, Union[bool, int]]:
        '''Main function of the class, it performs the validation of a :ref:`CBR <cbr>`
        and builds the :doc:`CBRGraph <cbrg>`.

        The validation process is implemented in two stages: firstly, a JSON Schema
        validation is performed, and, secondly, validating rules are sequentially
        applied to ensure that the recipe document satisfies the :ref:`CBR <cbr>`
        definition.

        :param data: The :ref:`CBR <cbr>` to be validated
        :type data: dict[str, Any]
        :param store: A flag indicating whether the validated CBR and :doc:`CBRGraph
          <cbrg>` should be stored in database, defaults to :const:`False`
        :type store: bool, optional
        :return: A dictionary indicating the results of the validation process and,
          in case of `store` set to :code:`True`, the identifier of the stored
          :ref:`CBR <cbr>` under the :code:`'inserted_id'` key
        :rtype: dict[str, Union[bool, int]]
        '''
        jsonschema.validate(data, self.schema)
        self.graph.clear()
        result = self.apply_validation_rules(data)

        if store:
            r = self._store(data)

            if r:
                result['inserted_id'] = r
            else:
                logger.error('Storing CBR and/or CBRGraph unsuccessful')

        return result


if __name__ == '__main__':
    import time
    from cookbase.parsers import utils

    logger.info('Start logging')
    # recipe = db_handler.get_cbr({'info.name': 'Pizza mozzarella'})
    recipe_path = '../../resources/cbr/pizzaMozzarella.json'
    recipe = utils.parse_json_recipe(recipe_path)
    t1 = time.time()
    result = Validator().validate(recipe, store=True)

    if 'inserted_id' in result:
        logger.info('CBR and CBRGraph inserted with id ' + str(result['inserted_id']))

    t2 = time.time()
    logger.info('Recipe validation: ' + str(int((t2 - t1) * 1000)) + ' ms')
    logger.info(result)
