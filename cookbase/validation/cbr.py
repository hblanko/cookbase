from typing import Any, Dict, Optional, Union

import jsonschema
import requests
from attr import attrib, attrs
from cookbase.db import handler
from cookbase.db.exceptions import CBRGraphInsertionError, CBRInsertionError
from cookbase.graph.cbrgraph import CBRGraph
from cookbase.logging import logger
from cookbase.validation import rules
from cookbase.validation.globals import Definitions


@attrs
class ValidationResult:
    """A class used to handle the results produced by the :meth:`Validator.validate`
    method.

    :param bool schema_validated: A flag indicating if the evaluated :ref:`Cookbase
      Recipe (CBR) <cbr>` was valid against the given CBR Schema, defaults to
      :const:`True`
    :param rules_results: A dictionary whose keys are the names of the functions
      implementing the rules that were applied for evaluation, and the values are the
      :class:`rules.AppliedRuleResult` objects obtained after each rule application
    :type rules_results: dict[str, rules.AppliedRuleResult]
    :param cbrgraph: An object containing the :doc:`Cookbase Recipe Graph (CBRGraph)
      <cbrg>` data generated during validation
    :type cbrgraph: CBRGraph, optional
    :param storing_result:
    :type storing_result: handler.InsertCBRResult, optional

    """

    schema_validated: bool = attrib(default=True)
    rules_results: Dict[str, rules.AppliedRuleResult] = attrib(factory=dict)
    cbrgraph: Optional[CBRGraph] = attrib(default=None)
    storing_result: Optional[handler.InsertCBRResult] = attrib(default=None)

    def is_valid(self, strict: bool = True) -> bool:
        """Indicates whether the validation process is evaluated as valid or not.

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
        """
        if not self.schema_validated:
            return False

        # TODO: Exception in len(rules_results) == 0 case
        for i in self.rules_results.values():
            if not i.has_passed(strict):
                return False

        return True


class Validator:
    """A class that performs validation and :doc:`Cookbase Recipe Graph (CBRGraph)
    <cbrg>` construction of recipes in :ref:`Cookbase Recipe (CBR) <cbr>` format.

    :param schema_url: A URL to where the :ref:`CBR <cbr>` Schema is to be retrieved,
      defaults to :attr:`cookbase.validation.globals.Definitions.cbr_schema_url`
    :type schema_url: str, optional

    :raises Exception: The HTTP response from requesting the :ref:`CBR <cbr>` Schema is
      empty

    :ivar schema: The :ref:`CBR <cbr>` schema
    :vartype schema: dict[str, Any]

    """

    def __init__(self, schema_url: str = Definitions.cbr_schema_url):
        """Constructor method."""
        r = requests.get(schema_url)
        r.raise_for_status()

        if len(r.content) == 0:
            raise Exception("the HTTP response from requesting JSON Schema is empty")

        self.schema: Dict[str, Any] = r.json()

    def _store(
        self, cbr: Dict[str, Any], cbrgraph: CBRGraph = None
    ) -> handler.InsertCBRResult:
        """Stores a :ref:`CBR <cbr>` and its :doc:`CBRGraph <cbrg>` into database.

        The data is stored using the :data:`cookbase.db.handler.db_handler` object.

        :param cbr: The dictionary containing the validated :ref:`CBR <cbr>`
        :type cbr: dict[str, Any]
        :param cbrgraph: An instance of :class:`cookbase.graph.cbrgraph.CBRGraph`
          storing the :doc:`CBRGraph <cbrg>` data
        :type cbrgraph: CBRGraph, optional
        :return: A :class:`handler.InsertCBRResult` object with the insertion
          results
        :rtype: handler.InsertCBRResult
        """
        return handler.get_handler().insert_cbr(cbr, cbrgraph)

    def apply_validation_rules(self, cbr: Dict[str, Any]) -> ValidationResult:
        """Validates a :ref:`CBR <cbr>` against the set of definition rules.

        Validation rules defined in :mod:`cookbase.validation.rules` are applied
        sequentially to ensure that the recipe document satisfies the :ref:`CBR <cbr>`
        definition.

        :param cbr: The :ref:`CBR <cbr>` to be validated
        :type cbr: dict[str, Any]
        :return: The results from applying the set of validation rules
        :rtype: ValidationResult
        """
        result = ValidationResult()
        rule = "ingredients_are_valid"
        result.rules_results[rule] = getattr(rules.Semantics, rule)(cbr["ingredients"])
        rule = "foodstuff_and_appliance_references_are_consistent"
        result.rules_results[rule] = getattr(rules.Semantics, rule)(
            cbr["ingredients"], cbr["appliances"], cbr["preparation"]
        )
        rule = "processes_and_appliances_are_valid_and_processes_requirements_met"
        result.rules_results[rule] = getattr(rules.Semantics, rule)(
            cbr["appliances"], cbr["preparation"]
        )
        result.cbrgraph = CBRGraph()
        result.cbrgraph.build_graph(cbr)
        rule = "ingredients_used_exactly_once"
        result.rules_results[rule] = getattr(rules.Graph, rule)(result.cbrgraph)
        rule = "single_final_process"
        result.rules_results[rule] = getattr(rules.Graph, rule)(result.cbrgraph)
        rule = "appliances_not_in_conflict"
        result.rules_results[rule] = getattr(rules.Graph, rule)(result.cbrgraph)
        return result

    def validate(
        self, cbr: Dict[str, Any], store: bool = False, strict: bool = True
    ) -> ValidationResult:
        """Main function of the class, it performs the validation of a :ref:`CBR <cbr>`
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
        :param strict: A flag indicating the validation policy, defaults to
          :const:`True`
        :type strict: bool, optional
        :return: The results from applying the set of validation rules
        :rtype: ValidationResult
        """
        try:
            jsonschema.validate(cbr, self.schema)
        except jsonschema.exceptions.SchemaError as e:
            logger.error("Invalid CBR Schema: " + e.message)
            return ValidationResult(schema_validated=False)
        except jsonschema.exceptions.ValidationError as e:
            logger.error("CBR does not satisfy CBR Schema: " + e.message)
            return ValidationResult(schema_validated=False)

        result = self.apply_validation_rules(cbr)

        if not result.is_valid(strict):
            logger.error("CBR does not satisfy CBR validation rules")
        elif store:
            try:
                result.storing_result = self._store(cbr, result.cbrgraph)
            except (CBRInsertionError, CBRGraphInsertionError) as e:
                logger.error(e)
                result.storing_result = e.partial_result

        return result


if __name__ == "__main__":
    import time
    from cookbase.parsers import utils

    logger.info("Start logging")
    # recipe = handler.get_handler().get_cbr({'info.name': 'Pizza mozzarella'})
    recipe = utils.parse_cbr("../tests/resources/pizza-mozzarella.cbr")
    t1 = time.time()
    strict_policy = False
    result = Validator().validate(recipe, store=True, strict=strict_policy)

    if result.is_valid(strict_policy) and result.storing_result:
        logger.info(f"CBR and CBRGraph inserted with id {result.storing_result.cbr_id}")

    t2 = time.time()
    logger.info(f"Recipe validation: {int((t2 - t1) * 1000)} ms")
