"""A module implementing the validation rules required by
:class:`cookbase.validation.cbr.Validator`, following the premises exposed in the
:ref:`assumptions` section of this documentation.

The validation rules are subdivided in two classes, :class:`Semantics` and
:class:`Graph`. Although the different methods provide a certainly modular approach to
the application of the validation rules, they are implemented from a problem
optimization perspective, and attending to this priority in some cases several tests are
collapsed into a single function.

"""
from typing import Any, Dict, List

from attr import attrib, attrs
from cookbase.db import handler
from cookbase.graph.cbrgraph import CBRGraph
from cookbase.logging import logger
from cookbase.validation.globals import Definitions


@attrs
class AppliedRuleResult:
    """A class containing the results of applying a validation rule defined in the
    :mod:`cookbase.validation.rules` module.

    :param errors: Field containing all the errors produced during the application
      of a rule, defaults to an empty list :const:`[]`
    :type errors: list[str], optional
    :param warnings: Field containing all the warnings produced during the application
      of a rule, defaults to an empty list :const:`[]`
    :type warnings: list[str], optional

    """

    errors: List[str] = attrib(factory=list)
    warnings: List[str] = attrib(factory=list)

    def has_passed(self, strict: bool = True) -> bool:
        """Indicates whether the application of a rule resulted successful or not.

        The `strict` flag indicates the policy for the evaluation of the rule
        application results: if set to :const:`True` (the default), any registered
        warning or error will cause the evaluation not to be passed; if set to
        :const:`False`, only registering errors --disregarding on warnings-- will result
        in a negative evaluation.

        :param strict: A flag indicating the policy for the results evaluation,
          defaults to :const:`True`
        :type strict: bool, optional
        :return: A value indicating whether the application of a rule resulted
          successful (returning :const:`True`) or unsuccessful (returning
          :const:`False`)
        :rtype: bool
        """

        if not strict:
            if len(self.errors) == 0:
                return True
            else:
                return False
        else:
            if len(self.errors) == 0 and len(self.warnings) == 0:
                return True
            else:
                return False

    def include_result(self, result: "AppliedRuleResult"):
        self.errors.extend(result.errors)
        self.warnings.extend(result.warnings)


class Semantics:
    """A class that holds the set of methods that impose semantic conditions in order to
    validate a :ref:`Cookbase Recipe (CBR) <cbr>`.

    All messages notifying validation errors or warnings are passed to the
    :data:`cookbase.logging.logger` instance.

    """

    @staticmethod
    def ingredients_are_valid(ingredients: Dict[str, Any]) -> AppliedRuleResult:
        """Checks whether the :ref:`CBR Ingredients <cbr-ingredients>` present in a
        :ref:`CBR <cbr>` are correct and their respective :ref:`CBIs <cbi>` exist in the
        database.

        The following messages will be logged if the corresponding problems are found:

        - *Error*: A given :ref:`CBI <cbi>` is not found in the database by its
          identifier.
        - *Warning*: A given :ref:`CBR Ingredient <cbr-ingredients>`'s name does not
          match any name available from the its referred :ref:`CBI <cbi>` definition.

        :param ingredients: The dictionary containing the :code:`ingredients` property
          from the :ref:`CBR <cbr>` to be validated, which holds a set of :ref:`CBR
          Ingredients <cbr-ingredients>`
        :type ingredients: dict[str, Any]
        :return: An :class:`AppliedRuleResult` object containing the errors and warnings
          registered during rule application
        :rtype: AppliedRuleResult
        """
        result = AppliedRuleResult()
        db_handler = handler.get_handler()

        for i in ingredients.values():
            cbi = db_handler.get_cbi(i["cbiId"])
            if cbi is None:
                e = f'CBI with id {i["cbiId"]} does not exist in database'
                result.errors.append(e)
                logger.error(e)
            else:
                cbi_names = cbi["name"][i["name"]["language"]]

                if (
                    isinstance(cbi_names, list) and i["name"]["text"] not in cbi_names
                ) or (isinstance(cbi_names, str) and i["name"]["text"] != cbi_names):
                    w = (
                        f'Ingredient name {i["name"]["text"]} does not match any '
                        f'available name for CBI {i["cbiId"]}'
                    )
                    result.warnings.append(w)
                    logger.warning(w)

        return result

    @staticmethod
    def appliance_is_valid(
        appliance: Dict[str, Any], cba: Dict[str, Any]
    ) -> AppliedRuleResult:
        """Checks whether a :ref:`CBR Appliance <cbr-appliances>` is valid according to
        a given :ref:`Cookbase Appliance (CBA) <cba>`.

        The following messages will be logged if the corresponding problems are found:

        - *Warning*: The given :ref:`CBR Appliance <cbr-appliances>`'s name language
          code is not found in the :ref:`CBA <cba>` definition.
        - *Warning*: The given :ref:`CBR Appliance <cbr-appliances>`'s name does not
          match any name available from the :ref:`CBA <cba>` definition.

        :param appliance: A dictionary containing a :ref:`CBR Appliance
          <cbr-appliances>` from the :ref:`CBR <cbr>` to be validated
        :type appliance: dict[str, Any]
        :param cba: A dictionary containing the :ref:`CBA <cba>` referred by the
          :ref:`CBR Appliance <cbr-appliances>` contained in `appliance`
        :type cba: dict[str, Any]
        :return: An :class:`AppliedRuleResult` object containing the errors and warnings
          registered during rule application
        :rtype: AppliedRuleResult
        """
        result = AppliedRuleResult()

        try:
            cba_names = cba["name"][appliance["name"]["language"]]
        except KeyError as ke:
            w = (
                f"Language code '{ke.__str__()}' of appliance "
                f'"{appliance["name"]["text"]}" does not match any available language '
                f'code for CBA {appliance["cbaId"]}'
            )
            result.warnings.append(w)
            logger.warning(w)
        else:
            if (
                isinstance(cba_names, list)
                and appliance["name"]["text"] not in cba_names
            ) or (
                isinstance(cba_names, str) and appliance["name"]["text"] != cba_names
            ):
                w = (
                    f'Appliance name "{appliance["name"]["text"]}" does not match any '
                    f'available name for CBA {appliance["cbaId"]}'
                )
                result.warnings.append(w)
                logger.warning(w)

        return result

    @staticmethod
    def process_is_valid(
        process: Dict[str, Any], cbp: Dict[str, Any]
    ) -> AppliedRuleResult:
        """Checks whether a :ref:`CBR Process <cbr-preparation>` is valid according to
        a given :ref:`Cookbase Process (CBP) <cbp>`.

        The following messages will be logged if the corresponding problems are found:

        - *Warning*: The given :ref:`CBR Process <cbr-preparation>`'s name language
          code is not found in the :ref:`CBP <cbp>` definition.
        - *Warning*: The given :ref:`CBR Process <cbr-preparation>`'s name does not
          match any name available from the :ref:`CBP <cbp>` definition.

        :param process: A dictionary containing a :ref:`CBR Process <cbr-preparation>`
          from the :ref:`CBR <cbr>` to be validated
        :type process: dict[str, Any]
        :param cbp: A dictionary containing the :ref:`CBP <cbp>` referred by the
          :ref:`CBR Process <cbr-preparation>` contained in `process`
        :type cbp: dict[str, Any]
        :return: An :class:`AppliedRuleResult` object containing the errors and warnings
          registered during rule application
        :rtype: AppliedRuleResult
        """
        result = AppliedRuleResult()

        try:
            cbp_names = cbp["name"][process["name"]["language"]]
        except KeyError as ke:
            w = (
                f"Language code '{ke.__str__()}' of process "
                f'"{process["name"]["text"]}" does not match any available language '
                f'code for CBP {process["cbpId"]}'
            )
            result.warnings.append(w)
            logger.warning(w)
        else:
            if (
                isinstance(cbp_names, list) and process["name"]["text"] not in cbp_names
            ) or (isinstance(cbp_names, str) and process["name"]["text"] != cbp_names):
                w = (
                    f'Process name "{process["name"]["text"]}" does not match any '
                    f'available name for CBP {process["cbpId"]}'
                )
                result.warnings.append(w)
                logger.warning(w)

        return result

    @staticmethod
    def processes_are_valid(processes: Dict[str, Any]) -> AppliedRuleResult:
        """Checks whether the :ref:`CBR Processes <cbr-preparation>` present in a
        :ref:`CBR <cbr>` are correct and their respective :ref:`CBPs <cbp>` exist in the
        database.

        The following messages will be logged if the corresponding problems are found:

        - *Error*: A given :ref:`CBP <cbp>` is not found in the database by its
          identifier.
        - Messages from the :meth:`process_is_valid` calls.

        .. note::
           Do not call if
           :meth:`processes_and_appliances_are_valid_and_processes_requirements_met` is
           executed, as this test will be redundant.

        :param processes: The dictionary containing the :code:`preparation` property
          from the :ref:`CBR <cbr>` to be validated, which holds a set of :ref:`CBR
          Processes <cbr-preparation>`
        :type processes: dict[str, Any]
        :return: An :class:`AppliedRuleResult` object containing the errors and warnings
          registered during rule application
        :rtype: AppliedRuleResult
        """
        result = AppliedRuleResult
        db_handler = handler.get_handler()

        for i in processes.values():
            cbp = db_handler.get_cbp(i["cbpId"])

            if cbp is None:
                e = f'CBP with id {i["cbpId"]} does not exist in database'
                result.errors.append(e)
                logger.error(e)
            else:
                partial_result = Semantics.process_is_valid(i, cbp)
                result.include_result(partial_result)

        return result

    @staticmethod
    def foodstuff_and_appliance_references_are_consistent(
        ingredients: Dict[str, Any],
        appliances: Dict[str, Any],
        processes: Dict[str, Any],
    ) -> AppliedRuleResult:
        """Checks for the consistency of a :ref:`CBR <cbr>` on the scope of its
        :ref:`CBR Ingredient <cbr-ingredients>`, :ref:`CBR Appliance <cbr-appliances>`
        and :ref:`CBR Process <cbr-preparation>` references.

        The function checks if:

        1. All foodstuff and appliance references appearing in the :ref:`CBR Processes
           <cbr-preparation>` exist in the context of the given :ref:`CBR <cbr>` (which
           may either be references to :ref:`CBR Ingredients <cbr-ingredients>`,
           :ref:`CBR Appliances <cbr-appliances>` or :ref:`CBR Processes
           <cbr-preparation>`, as explained in the :doc:`Cookbase Data Model (CBDM)
           documentation <cbdm>` on the :code:`preparation` section of a :ref:`CBR
           <cbr>`).
        2. There are no unreferenced :ref:`CBR Ingredients <cbr-ingredients>` or
           :ref:`CBR Appliances <cbr-appliances>` in the given :ref:`CBR <cbr>`.

        The following messages will be logged if the corresponding problems are found:

        - *Error*: There is no :ref:`CBR Ingredient <cbr-ingredients>` nor :ref:`CBR
          Process <cbr-preparation>` matching a foodstuff reference from a :ref:`CBR
          Process <cbr-preparation>` in the given :ref:`CBR <cbr>`.
        - *Error*: There is no :ref:`CBR Appliance <cbr-appliances>` matching an
          appliance reference from a :ref:`CBR Process <cbr-preparation>` in the given
          :ref:`CBR <cbr>`.
        - *Warning*: A :ref:`CBR Ingredient <cbr-ingredients>` is not referenced by any
          :ref:`CBR Process <cbr-preparation>` in the given :ref:`CBR <cbr>`.
        - *Warning*: A :ref:`CBR Appliance <cbr-appliances>` is not referenced by any
          :ref:`CBR Process <cbr-preparation>` in the given :ref:`CBR <cbr>`.

        :param ingredients: The dictionary containing the :code:`ingredients` property
          from the :ref:`CBR <cbr>` to be validated, which holds a set of :ref:`CBR
          Ingredients <cbr-ingredients>`
        :type ingredients: dict[str, Any]
        :param appliances: The dictionary containing the :code:`appliances` property
          from the :ref:`CBR <cbr>` to be validated, which holds a set of :ref:`CBR
          Appliances <cbr-appliances>`
        :type ingredients: dict[str, Any]
        :param processes: The dictionary containing the :code:`preparation` property
          from the :ref:`CBR <cbr>` to be validated, which holds a set of :ref:`CBR
          Processes <cbr-preparation>`
        :type processes: dict[str, Any]
        :return: An :class:`AppliedRuleResult` object containing the errors and warnings
          registered during rule application
        :rtype: AppliedRuleResult
        """
        result = AppliedRuleResult()
        used_ingredients = set()
        used_appliances = set()

        for i in processes.values():
            # Checking foodstuffs references
            for j in [v for v in Definitions.foodstuff_keywords if v in i.keys()]:
                r = i[j]

                if isinstance(r, str):
                    if r not in ingredients.keys():
                        if r not in processes.keys():
                            e = (
                                f"Foodstuff reference '{r}' appears neither in "
                                f"'ingredients' nor in 'preparation' section"
                            )
                            result.errors.append(e)
                            logger.error(e)
                    else:
                        used_ingredients.add(r)
                else:
                    for q in r:
                        if q not in ingredients.keys():
                            if q not in processes.keys():
                                e = (
                                    f"Foodstuff reference '{q}' appears neither in "
                                    f"'ingredients' nor in 'preparation' section"
                                )
                        else:
                            used_ingredients.add(q)

            # Checking appliances references
            for a in i["appliances"]:
                if a["appliance"] not in appliances.keys():
                    e = (
                        f'Appliance reference \'{a["appliance"]}\' does not appear in '
                        f"'appliances' section"
                    )
                    result.errors.append(e)
                    logger.error(e)
                else:
                    used_appliances.add(a["appliance"])

        # Checking unused ingredients
        diff = ingredients.keys() - used_ingredients

        for d in diff:
            w = f"Ingredient '{d}' is not used in 'preparation' section"
            result.warnings.append(w)
            logger.warning(w)

        # Checking unused appliances
        diff = appliances.keys() - used_appliances

        for d in diff:
            w = f"Appliance '{d}' is not used in 'preparation' section"
            result.warnings.append(w)
            logger.warning(w)

        return result

    @staticmethod
    def cbas_satisfy_cbp(
        cbas: List[Dict[str, Any]], cbp: Dict[str, Any]
    ) -> AppliedRuleResult:
        """Checks if a set of :ref:`CBAs <cba>` satisfy at least one of the condition
        clauses provided by the :code:`data.validation.conditions.requiredAppliances`
        property of a given :ref:`CBP <cbp>`.

        The provided :ref:`CBAs <cba>` are assumed to exist in the database.

        :param cbas: A list containing the :ref:`CBAs <cba>` to be verified
        :type cbas: list[dict[str, Any]]
        :param cbp: The dictionary containing the :ref:`CBP <cbp>` whose conditions
          clauses are to be checked for satisfaction
        :type cbp: dict[str, Any]
        :return: An :class:`AppliedRuleResult` object containing the errors and warnings
          registered during rule application
        :rtype: AppliedRuleResult
        """
        from cookbase.validation.cba import unroll

        unrolled_cbas = [unroll(cba) for cba in cbas]

        for clause in cbp["info"]["validation"]["conditions"]["requiredAppliances"]:
            unsatisfied_clause = False
            satisfied_literals = [False] * len(clause)
            satisfying_cbas = [False] * len(unrolled_cbas)

            # First iteration searching for exact cbaIds
            # in order to minimize the search space
            for i in range(len(clause)):
                literal = clause[i]
                if "cbaId" in literal:
                    for j in range(len(unrolled_cbas)):
                        if satisfying_cbas[j]:
                            continue

                        if (
                            isinstance(unrolled_cbas[j]["id"], int)
                            and unrolled_cbas[j]["id"] == literal["cbaId"]
                        ) or (
                            isinstance(unrolled_cbas[j]["id"], list)
                            and literal["cbaId"] in unrolled_cbas[j]["id"]
                        ):
                            satisfied_literals[i] = True
                            satisfying_cbas[j] = True
                            break

                    if not satisfied_literals[i]:
                        unsatisfied_clause = True
                        break

            if unsatisfied_clause:
                continue

            # Second iteration searching for functions

            # TODO: search combinatorial space exhaustively
            ###############################################
            # This implementation may throw false negatives
            # as it associates a CBA to a CBP literal function
            # sequentially, not considering any rearrangement
            # that may lead us to a solution.
            ############################
            for i in range(len(clause)):
                if satisfied_literals[i]:
                    continue

                literal = clause[i]
                if "function" in literal:
                    for j in range(len(unrolled_cbas)):
                        if satisfying_cbas[j]:
                            continue

                        if literal["function"] in unrolled_cbas[j]["info"]["functions"]:
                            satisfied_literals[i] = True
                            satisfying_cbas[j] = True
                            break

                    if not satisfied_literals[i]:
                        unsatisfied_clause = True
                        break

            if not unsatisfied_clause:
                return AppliedRuleResult()

        e = f'Appliance requirements of CBP {cbp["id"]} are not satisfied'
        logger.error(e)
        return AppliedRuleResult(errors=[e])

    @staticmethod
    def processes_and_appliances_are_valid_and_processes_requirements_met(
        appliances: Dict[str, Any], processes: Dict[str, Any]
    ) -> AppliedRuleResult:
        """Checks correctness and consistency on the :ref:`CBR Appliances
        <cbr-appliances>` and :ref:`CBR Processes <cbr-preparation>` present in a
        :ref:`CBR <cbr>`.

        The function checks if:

        1. All :ref:`CBR Appliances <cbr-appliances>` and :ref:`CBR Processes
           <cbr-preparation>` are correct and their respective :ref:`CBAs <cba>` and
           :ref:`CBPs <cbp>` exist in the database.
        2. All :ref:`CBR Processes <cbr-preparation>` find there appliance requirements
           met.

        The following messages will be logged if the corresponding problems are found:

        - *Error*: A given :ref:`CBA <cba>` is not found in the database by its
          identifier.
        - *Error*: A given :ref:`CBP <cbp>` is not found in the database by its
          identifier.
        - *Error*: The appliance requirements of a given :ref:`CBR Process
          <cbr-preparation>` are not met.
        - Messages from the :meth:`appliance_is_valid` and :meth:`process_is_valid`
          calls.

        :param appliances: The dictionary containing the :code:`appliances` property
          from the :ref:`CBR <cbr>` to be validated, which holds a set of :ref:`CBR
          Appliances <cbr-appliances>`
        :type appliances: dict[str, Any]
        :param processes: The dictionary containing the :code:`preparation` property
          from the :ref:`CBR <cbr>` to be validated, which holds a set of :ref:`CBR
          Processes <cbr-preparation>`
        :type processes: dict[str, Any]
        :return: An :class:`AppliedRuleResult` object containing the errors and warnings
          registered during rule application
        :rtype: AppliedRuleResult
        """
        result = AppliedRuleResult()
        db_handler = handler.get_handler()

        for process_reference, p in processes.items():
            # Checking CBP validity
            cbp = db_handler.get_cbp(p["cbpId"])

            if cbp is None:
                e = f'CBP with id {p["cbpId"]} does not exist in database'
                result.errors.append(e)
                logger.error(e)
            else:
                partial_result = Semantics.process_is_valid(p, cbp)
                result.include_result(partial_result)

            # Checking CBAs validity
            cbas = []

            for a in p["appliances"]:
                if "cbaId" in appliances[a["appliance"]]:
                    cba = db_handler.get_cba(appliances[a["appliance"]]["cbaId"])

                    if cba is None:
                        e = (
                            f'CBA with id {appliances[a["appliance"]]["cbaId"]} does '
                            f"not exist in database"
                        )
                        result.errors.append(e)
                        logger.error(e)
                        continue
                    else:
                        partial_result = Semantics.appliance_is_valid(
                            appliances[a["appliance"]], cba
                        )
                        result.include_result(partial_result)
                else:
                    cba = {
                        "id": None,
                        "info": {
                            "familyLevel": 0,
                            "functions": appliances[a["appliance"]]["functions"],
                        },
                    }

                cbas.append(cba)

            # Checking whether process requirements are met
            partial_result = Semantics.cbas_satisfy_cbp(cbas, cbp)
            result.include_result(partial_result)

        return result


class Graph:
    """A class that holds the set of methods that impose graph consistency conditions in
    order to validate a :ref:`Cookbase Recipe (CBR) <cbr>` analyzing its corresponding
    :doc:`Cookbase Recipe Graph (CBRGraph) <cbrg>`.

    All messages notifying validation errors or warnings are passed to the
    :data:`cookbase.logging.logger` instance.

    """

    @staticmethod
    def ingredients_used_exactly_once(graph: CBRGraph) -> AppliedRuleResult:
        """Checks that every :ref:`CBR Ingredient <cbr-ingredients>` in a given
        :doc:`CBRGraph <cbrg>` is directly used by a :ref:`CBR Process
        <cbr-preparation>` exactly once.

        The following messages will be logged if the corresponding problems are found:

        - *Error*: A given :ref:`CBR Ingredient <cbr-ingredients>` is used more than
          once in the :code:`preparation` section of the analyzed :ref:`CBR <cbr>`.
        - *Warning*: A given :ref:`CBR Ingredient <cbr-ingredients>` is not used in the
          :code:`preparation` section of the analyzed :ref:`CBR <cbr>`.

        :param graph: The :doc:`CBRGraph <cbrg>` generated from the :ref:`CBR <cbr>` to
          be validated
        :type graph: cookbase.graph.cbrgraph.CBRGraph
        :return: An :class:`AppliedRuleResult` object containing the errors and warnings
          registered during rule application
        :rtype: AppliedRuleResult
        """
        result = AppliedRuleResult()

        for i in graph.get_ingredients():
            r = graph.g.out_degree(i)

            if r == 0:
                w = f"Ingredient '{i}' is not used during preparation"
                result.warnings.append(w)
                logger.warning(w)
            elif r > 1:
                e = f"Ingredient '{i}' is used more than once during preparation"
                result.errors.append(e)
                logger.error(e)

        return result

    @staticmethod
    def single_final_process(graph: CBRGraph) -> AppliedRuleResult:
        """Checks if there is only one :ref:`CBR Process <cbr-preparation>` in a given
        :doc:`CBRGraph <cbrg>` acting as the end process.

        The following messages will be logged if the corresponding problems are found:

        - *Error*: There are more than one ending :ref:`CBR Process <cbr-preparation>`
          in the analyzed :ref:`CBR <cbr>`.

        :param graph: The :doc:`CBRGraph <cbrg>` generated from the :ref:`CBR <cbr>` to
          be validated
        :type graph: cookbase.graph.cbrgraph.CBRGraph
        :return: An :class:`AppliedRuleResult` object containing the errors and warnings
          registered during rule application
        :rtype: AppliedRuleResult
        """
        result = AppliedRuleResult()

        if len(graph.get_leaf_processes()) > 1:
            e = f"There are more than one ending processes in the recipe"
            result.errors.append(e)
            logger.error(e)

        return result

    @staticmethod
    def appliances_not_in_conflict(graph: CBRGraph) -> AppliedRuleResult:
        """Checks whether there are not any :ref:`CBR Appliance <cbr-appliances>` in a
        given :doc:`CBRGraph <cbrg>` that may be in conflict, that is, potentially used
        by two or more concurrent :ref:`CBR Processes <cbr-preparation>` at the same
        time.

        The following messages will be logged if the corresponding problems are found:

        - *Warning*: A :ref:`CBR Appliance <cbr-appliances>` is required by more than
          one concurrent :ref:`CBR Process <cbr-preparation>` in the analyzed :ref:`CBR
          <cbr>`.

        :param graph: The :doc:`CBRGraph <cbrg>` generated from the :ref:`CBR <cbr>` to
          be validated
        :type graph: cookbase.graph.cbrgraph.CBRGraph
        :return: An :class:`AppliedRuleResult` object containing the errors and warnings
          registered during rule application
        :rtype: AppliedRuleResult
        """
        result = AppliedRuleResult()
        ag = graph.aggregated_appliances_graph()
        concurrent_paths = [i for i, _ in ag.in_degree() if _ == 0]

        while concurrent_paths:
            # Checks all combinations of two concurrent paths
            for i in range(len(concurrent_paths) - 1):
                for j in range(i + 1, len(concurrent_paths)):
                    appls_1 = ag.nodes[concurrent_paths[i]]["appliances"].keys()
                    appls_2 = ag.nodes[concurrent_paths[j]]["appliances"].keys()
                    conflicting_appliances = appls_1 & appls_2

                    if conflicting_appliances:
                        for k in conflicting_appliances:
                            s = "("

                            for p in ag.nodes[concurrent_paths[i]]["appliances"][k]:
                                s += f"'{p}', "

                            s = s.rpartition(", ")[0] + ") and ("

                            for p in ag.nodes[concurrent_paths[j]]["appliances"][k]:
                                s += f"'{p}', "

                            s = s.rpartition(", ")[0] + ")"

                            w = (
                                f"Appliance '{k}' is used in potentially concurrent "
                                f"processes {s}"
                            )
                            result.warnings.append(w)
                            logger.warning(w)

            # Updates concurrent paths
            candidates_next = set()

            for i in concurrent_paths:
                for s in ag.successors(i):
                    candidates_next.add(s)

            next_cp = set()
            cp_helper_set = set(concurrent_paths)

            for i in candidates_next:
                advances = True

                for j in ag.predecessors(i):
                    if j not in cp_helper_set:
                        advances = False
                        break

                if advances:
                    next_cp.add(i)
                else:
                    for j in ag.predecessors(i):
                        if j in cp_helper_set:
                            next_cp.add(j)

            concurrent_paths = list(next_cp)

        return result
