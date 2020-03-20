from typing import Any, Dict, Optional, Union

import jsonschema
import requests
from attr import attrib, attrs
from cookbase.db import handler
from cookbase.graph.recipegraph import RecipeGraph
from cookbase.logging import logger
from cookbase.validation import rules
from cookbase.validation.globals import Definitions


@attrs
class ValidationResult():
    '''A class used to handle the results produced by the :meth:`Validator.validate`
    method.

    :param rules_results: A dictionary whose keys are the names of the functions
      implementing the rules that were applied for evaluation, and the values are the
      :class:`rules.AppliedRuleResult` objects obtained after each rule application
    :type rules_results: dict[str, rules.AppliedRuleResult]
    :param cbrgraph: An object containing the :doc:`Cookbase Recipe Graph (CBRGraph)
      <cbrg>` data generated during validation
    :type cbrgraph: RecipeGraph, optional
    :param storing_result: 
    :type storing_result: handler.DBHandler.InsertCBRResult, optional

    '''
    rules_results: Dict[str, rules.AppliedRuleResult] = attrib(factory=dict)
    cbrgraph: Optional[RecipeGraph] = attrib(default=None)
    storing_result: Optional[handler.DBHandler.InsertCBRResult] = attrib(default=None)

    def is_valid(self, strict: bool = True) -> bool:
        '''Indicates whether the validation process is evaluated as valid or not.

        The `strict` flag indicates the policy for the evaluation of the rule
        application results: if set to :const:`True` (the default), any registered
        warning or error from any rule will cause the evaluation invalid; if set to
        :const:`False`, only registering errors --disregarding on warnings-- will result
        in a negative evaluation.

        :param strict: A flag indicating the validation policy, defaults to
          :const:`True`
        :type strict: bool, optional
        :return: A value indicating whether the validation resulted successful
          (returning :const:`True`) or unsuccessful (returning :const:`False`)
        :rtype: bool
        '''
        # TODO: Exception in len(rules_results) == 0 case
        for i in self.rules_results.values():
            if not i.has_passed(strict=strict):
                return False

        return True


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

    '''

    def __init__(self, schema_url: str = Definitions.cbr_schema_url):
        '''Constructor method.'''
        r = requests.get(schema_url)
        r.raise_for_status()

        if len(r.content) == 0:
            raise Exception('the HTTP response from requesting JSON Schema is empty')

        self.schema: Dict[str, Any] = r.json()

    def _store(self, cbr: Dict[str, Any],
               cbrgraph: RecipeGraph = None) -> Union[int, bool]:
        '''Stores a :ref:`CBR <cbr>` and its :doc:`CBRGraph <cbrg>` into database.

        The data is stored using the :data:`cookbase.db.handler.db_handler` object.

        :param cbr: The dictionary containing the validated :ref:`CBR <cbr>`
        :type cbr: dict[str, Any]
        :param cbrgraph: An instance of :class:`cookbase.graph.recipegraph.RecipeGraph`
          storing the :doc:`CBRGraph <cbrg>` data
        :type cbrgraph: RecipeGraph, optional
        :return: If :ref:`CBR <cbr>` and :doc:`CBRGraph <cbrg>` insertions were
          successful returns the identifier of the stored object, returns :const:`False`
          otherwise
        :rtype: int or bool
        '''
        if cbrgraph:
            return handler.get_handler().insert_cbr(cbr,
                                                    cbrgraph.get_serializable_graph())
        else:
            return handler.get_handler().insert_cbr(cbr)

    def apply_validation_rules(self, cbr: Dict[str, Any]) -> ValidationResult:
        '''Validates a :ref:`CBR <cbr>` against the set of definition rules.

        Validation rules defined in :mod:`cookbase.validation.rules` are applied
        sequentially to ensure that the recipe document satisfies the :ref:`CBR <cbr>`
        definition.

        :param cbr: The :ref:`CBR <cbr>` to be validated
        :type cbr: dict[str, Any]
        :return: The results from applying the set of validation rules
        :rtype: ValidationResult
        '''
        result = ValidationResult()
        rule = 'ingredients_are_valid'
        result.rules_results[rule] = getattr(rules.Semantics, rule)(cbr['ingredients'])
        rule = 'foodstuff_and_appliance_references_are_consistent'
        result.rules_results[rule] = getattr(rules.Semantics, rule)(
            cbr['ingredients'],
            cbr['appliances'],
            cbr['preparation']
        )
        rule = 'processes_and_appliances_are_valid_and_processes_requirements_met'
        result.rules_results[rule] = getattr(rules.Semantics, rule)(cbr['appliances'],
                                                                    cbr['preparation'])
        result.cbrgraph = RecipeGraph()
        result.cbrgraph.build_graph(cbr)
        rule = 'ingredients_used_exactly_once'
        result.rules_results[rule] = getattr(rules.Graph, rule)(result.cbrgraph)
        rule = 'single_final_process'
        result.rules_results[rule] = getattr(rules.Graph, rule)(result.cbrgraph)
        rule = 'appliances_not_in_conflict'
        result.rules_results[rule] = getattr(rules.Graph, rule)(result.cbrgraph)
        return result

    def validate(self,
                 cbr: Dict[str, Any],
                 store: bool = False) -> ValidationResult:
        '''Main function of the class, it performs the validation of a :ref:`CBR <cbr>`
        and builds the :doc:`CBRGraph <cbrg>`.

        The validation process is implemented in two stages: firstly, a JSON Schema
        validation is performed, and, secondly, validating rules are sequentially
        applied to ensure that the recipe document satisfies the :ref:`CBR <cbr>`
        definition.

        :param cbr: The :ref:`CBR <cbr>` to be validated
        :type cbr: dict[str, Any]
        :param store: A flag indicating whether the validated CBR and :doc:`CBRGraph
          <cbrg>` should be stored in database, defaults to :const:`False`
        :type store: bool, optional
        :return: The results from applying the set of validation rules
        :rtype: ValidationResult
        '''
        jsonschema.validate(cbr, self.schema)
        result = self.apply_validation_rules(cbr)

        if store and result.is_valid(strict=False):
            r = self._store(cbr, result.cbrgraph)

            if r:
                result.storing_result = r
            else:
                logger.error('Storing CBR and/or CBRGraph unsuccessful')
        elif not result.is_valid(strict=False):
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

    if result.storing_result:
        logger.info(f'CBR and CBRGraph inserted with id {result.storing_result.cbr_id}')

    t2 = time.time()
    logger.info(f'Recipe validation: {int((t2 - t1) * 1000)} ms')
