from typing import Any, Dict

from cookbase.db.handler import db_handler
from cookbase.graph.recipegraph import RecipeGraph
from cookbase.validation.globals import Definitions
from cookbase.validation.logger import logger


class Semantics():
    """Class containing a number of methods that impose semantic conditions in order to validate a CBR."""
    @staticmethod
    def cbis_are_valid(ingredients: Dict[str, Any]) -> bool:
        ret = True
        for i in ingredients.values():
            cbi = db_handler.get_cbi(i["cbiId"])
            if cbi is None:
                ret = False
                logger.error("CBI with id " +
                             str(i["cbiId"]) +
                             " does not exist in database")
            else:
                cbi_names = cbi["name"][i["name"]["language"]]
                if (isinstance(cbi_names, list) and i["name"]["text"] not in cbi_names) or (
                        isinstance(cbi_names, str) and i["name"]["text"] != cbi_names):
                    ret = False
                    logger.warning("Ingredient name '" +
                                   i["name"]["text"] +
                                   "' does not match any available name for CBI " +
                                   str(i["cbiId"]))
        return ret

    @staticmethod
    def cba_is_valid(
            appliance: Dict[str, Any], cba: Dict[str, Any]) -> bool:
        ret = True
        try:
            cba_names = cba["name"][appliance["name"]["language"]]
        except KeyError as ke:
            ret = False
            logger.warning("Language code " + ke.__str__() + " of appliance '" +
                           appliance["name"]["text"] +
                           "' does not match any available language code for CBA " +
                           str(appliance["cbaId"]))
        else:
            if (isinstance(cba_names, list) and appliance["name"]["text"] not in cba_names) or (
                    isinstance(cba_names, str) and appliance["name"]["text"] != cba_names):
                ret = False
                logger.warning("Appliance name '" +
                               appliance["name"]["text"] +
                               "' does not match any available name for CBA " +
                               str(appliance["cbaId"]))
        return ret

    @staticmethod
    def cbp_is_valid(
            process: Dict[str, Any], cbp: Dict[str, Any]) -> bool:
        ret = True
        try:
            cbp_names = cbp["name"][process["name"]["language"]]
        except KeyError as ke:
            ret = False
            logger.warning("Language code " + ke.__str__() + " of process '" +
                           process["name"]["text"] +
                           "' does not match any available language code for CBP " +
                           str(process["cbpId"]))
        else:
            if (isinstance(cbp_names, list) and process["name"]["text"] not in cbp_names) or (
                    isinstance(cbp_names, str) and process["name"]["text"] != cbp_names):
                ret = False
                logger.warning("Process name '" +
                               process["name"]["text"] +
                               "' does not match any available name for CBP " +
                               str(process["cbpId"]))
        return ret

    # Do not call if cbps_and_cbas_are_valid_and_processes_requirements_met()
    # is called, which already performs the same check.
    @staticmethod
    def cbps_are_valid(processes: Dict[str, Any]) -> bool:
        ret = True
        for i in processes.values():
            cbp = db_handler.get_cbp(i["cbpId"])
            if cbp is None:
                ret = False
                logger.error("CBP with id " +
                             str(i["cbpId"]) +
                             " does not exist in database")
            else:
                ret = ret and Semantics.cbp_is_valid(i, cbp)
        return ret

    @staticmethod
    def foodstuff_and_appliance_references_are_consistent(
            ingredients: Dict[str, Any],
            appliances: Dict[str, Any],
            processes: Dict[str, Any]) -> bool:
        ret = True
        used_ingredients = set()
        used_appliances = set()
        for i in processes.values():
            # Checking foodstuffs references
            for j in [
                    v for v in Definitions.foodstuff_keywords if v in i.keys()]:
                r = i[j]
                if isinstance(r, str):
                    if r not in ingredients.keys():
                        if r not in processes.keys():
                            ret = False
                            logger.error(
                                "Foodstuff reference '" + r + "' appears neither in 'ingredients' nor in 'preparation' section")
                    else:
                        used_ingredients.add(r)
                else:
                    for q in r:
                        if q not in ingredients.keys():
                            if q not in processes.keys():
                                ret = False
                                logger.error(
                                    "Foodstuff reference '" + q + "' appears neither in 'ingredients' nor in 'preparation' section")
                        else:
                            used_ingredients.add(q)
            # Checking appliances references
            for a in i["appliances"]:
                if a["appliance"] not in appliances.keys():
                    ret = False
                    logger.error(
                        "Appliance reference '" + a["appliance"] + "' does not appear in 'appliances' section")
                else:
                    used_appliances.add(a["appliance"])
        # Checking unused ingridients
        diff = ingredients.keys() - used_ingredients
        for d in diff:
            ret = False
            logger.warning(
                "Ingredient '" + d + "' is not used in 'preparation' section")
        # Checking unused appliances
        diff = appliances.keys() - used_appliances
        for d in diff:
            ret = False
            logger.warning(
                "Appliance '" + d + "' is not used in 'preparation' section")
        return ret

    @staticmethod
    def cbas_satisfy_cbp(
            cbas: Dict[str, Any],
            cbp: Dict[str, Any]) -> bool:
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
                        if (isinstance(unrolled_cbas[j]["id"], int) and unrolled_cbas[j]["id"] == literal["cbaId"]) or (
                                isinstance(unrolled_cbas[j]["id"], list) and literal["cbaId"] in unrolled_cbas[j]["id"]):
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
            ######################
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
                return True
        return False

    @staticmethod
    def cbps_and_cbas_are_valid_and_processes_requirements_met(
            appliances: Dict[str, Any],
            processes: Dict[str, Any]) -> bool:
        ret = True
        for process_reference, p in processes.items():
            # Checking CBP validity
            cbp = db_handler.get_cbp(p["cbpId"])
            if cbp is None:
                ret = False
                logger.error("CBP with id " +
                             str(p["cbpId"]) +
                             " does not exist in database")
            else:
                ret = ret and Semantics.cbp_is_valid(p, cbp)
            # Checking CBAs validity
            cbas = list()
            for a in p["appliances"]:
                if "cbaId" in appliances[a["appliance"]]:
                    cba = db_handler.get_cba(
                        appliances[a["appliance"]]["cbaId"])
                    if cba is None:
                        ret = False
                        logger.error("CBA with id " +
                                     str(appliances[a["appliance"]]["cbaId"]) +
                                     " does not exist in database")
                        continue
                    else:
                        ret = ret and Semantics.cba_is_valid(
                            appliances[a["appliance"]], cba)
                else:
                    cba = {
                        "id": None,
                        "info": {
                            "familyLevel": 0,
                            "functions": appliances[a["appliance"]]["functions"]
                        }
                    }
                cbas.append(cba)
            # Checking whether process requirements are met
            if not Semantics.cbas_satisfy_cbp(cbas, cbp):
                logger.error(
                    "Appliance requirements of process '" + process_reference + "' are not satisfied")
                ret = False
        return ret


class Graph():
    """Class containing a number of methods that impose graph consistency conditions in order to validate a CBR."""

    @staticmethod
    def ingredients_used_only_once(graph: RecipeGraph) -> bool:
        ret = True
        for i in graph.get_ingredients():
            r = graph.g.out_degree(i)
            if r == 0:
                logger.warning(
                    "Ingredient '" + i + "' is not used during preparation")
                ret = False
            elif r > 1:
                logger.error(
                    "Ingredient '" + i + "' is used more than once during preparation")
                ret = False
        return ret

    @staticmethod
    def single_final_process(graph: RecipeGraph) -> bool:
        ret = len(graph.get_leaf_processes()) == 1
        if not ret:
            logger.error(
                "There are more than one ending processes in the recipe")
        return ret

    @staticmethod
    def appliances_not_in_conflict(graph: RecipeGraph) -> bool:
        ret = True
        ag = graph.aggregated_appliances_graph()
        concurrent_paths = [i for i, _ in ag.in_degree() if _ == 0]

        while concurrent_paths:
            # Checks all combinations of two concurrent paths
            for i in range(len(concurrent_paths) - 1):
                for j in range(i + 1, len(concurrent_paths)):
                    appls_1 = ag.nodes[concurrent_paths[i]
                                       ]["appliances"].keys()
                    appls_2 = ag.nodes[concurrent_paths[j]
                                       ]["appliances"].keys()
                    conflicting_appliances = appls_1 & appls_2
                    if conflicting_appliances:
                        ret = False
                        for k in conflicting_appliances:
                            s = "("
                            for p in ag.nodes[concurrent_paths[i]
                                              ]["appliances"][k]:
                                s += "'" + p + "', "
                            s = s.rpartition(", ")[0] + ") and ("
                            for p in ag.nodes[concurrent_paths[j]
                                              ]["appliances"][k]:
                                s += "'" + p + "', "
                            s = s.rpartition(", ")[0] + ")"
                            logger.warning(
                                "Appliance '" + k + "' is used in potentially concurrent processes " + s)

            #
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

        return ret
