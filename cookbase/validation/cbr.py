from typing import Any, Dict, Union

import jsonschema
import requests
from cookbase.db import handler
from cookbase.graph.recipegraph import RecipeGraph
from cookbase.logging import logger
from cookbase.validation import rules
from cookbase.validation.globals import Definitions


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

    def __init__(self, schema_url: str = Definitions.cbr_schema_url):
        '''Constructor method.'''
        r = requests.get(schema_url)
        r.raise_for_status()

        if len(r.content) == 0:
            raise Exception('the HTTP response from requesting JSON Schema is empty')

        self.schema: Dict[str, Any] = r.json()
        self.graph: RecipeGraph = RecipeGraph()

    def _store(self, data: Dict[str, Any]) -> Union[int, bool]:
        '''Stores a :ref:`CBR <cbr>` and its :doc:`CBRGraph <cbrg>` into database.

        The data is stored using the :data:`cookbase.db.handler.db_handler` object.

        :param data: The dictionary containing the validated :ref:`CBR <cbr>`
        :type data: dict[str, Any]
        :return: If :ref:`CBR <cbr>` and :doc:`CBRGraph <cbrg>` insertion was successful
          returns the identifier of the stored object, returns :const:`False` otherwise
        :rtype: int or bool
        '''
        return handler.get_handler().insert_cbr(data,
                                                self.graph.get_serializable_graph())

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
        rule = 'ingredients_are_valid'
        result[rule] = getattr(rules.Semantics, rule)(
            data['ingredients']
        ).has_passed(strict=False)
        rule = 'foodstuff_and_appliance_references_are_consistent'
        result[rule] = getattr(rules.Semantics, rule)(
            data['ingredients'],
            data['appliances'],
            data['preparation']
        ).has_passed(strict=False)
        rule = 'processes_and_appliances_are_valid_and_processes_requirements_met'
        result[rule] = getattr(rules.Semantics, rule)(
            data['appliances'], data['preparation']
        ).has_passed(strict=False)
        self.graph.build_graph(data)
        rule = 'ingredients_used_exactly_once'
        result[rule] = getattr(rules.Graph, rule)(self.graph).has_passed(strict=False)
        rule = 'single_final_process'
        result[rule] = getattr(rules.Graph, rule)(self.graph).has_passed(strict=False)
        rule = 'appliances_not_in_conflict'
        result[rule] = getattr(rules.Graph, rule)(self.graph).has_passed(strict=False)
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

        if store and False not in result.values():
            r = self._store(data)

            if r:
                result['inserted_id'] = r
            else:
                logger.error('Storing CBR and/or CBRGraph unsuccessful')
        elif False in result.values():
            logger.error('CBR and CBRGraph not stored due to validation errors')

        return result


if __name__ == '__main__':
    import time
    from cookbase.parsers import utils

    logger.info('Start logging')
    # recipe = handler.get_handler().get_cbr({'info.name': 'Pizza mozzarella'})
    recipe = utils.parse_cbr('../tests/resources/pizza-mozzarella.cbr')
    t1 = time.time()
    result = Validator().validate(recipe, store=True)

    if 'inserted_id' in result:
        logger.info(f'CBR and CBRGraph inserted with id {result["inserted_id"]}')

    t2 = time.time()
    logger.info(f'Recipe validation: {int((t2 - t1) * 1000)} ms')
    logger.info(result)
