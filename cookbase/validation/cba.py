from typing import Any, Dict

from cookbase.db.handler import db_handler


def unroll(cba: Dict[str, Any]) -> Dict[str, Any]:
    """Returns an augmented CBA by retrieving parent CBAs recursively

    If the Cookbase Appliance has a parent, :func:`unroll` is recursively
    called returning an augmented structure with inherited data on
    `functions`, `materials`, and the id field updated to a list also
    including all the parent ids; if the Cookbase Appliance has no
    parents, it is returned with no modifications.

    :param cba: A CBA to be unrolled
    :type cba: dict[str, Any]
    :return: An augmented CBA
    :rtype: dict[str, Any]
    """
    try:
        if cba["info"]["familyLevel"] <= 1:
            return cba
        parent_cba = db_handler.get_cba(cba["info"]["parent"])
        if parent_cba["info"]["familyLevel"] > 1:
            parent_cba = unroll(parent_cba)
        if isinstance(parent_cba["id"], list):
            aggregated_id = parent_cba["id"] + [cba["id"]]
        else:
            aggregated_id = [parent_cba["id"], cba["id"]]
        cba["id"] = aggregated_id
        if "functions" in parent_cba["info"]:
            if "functions" not in cba["info"]:
                cba["info"]["functions"] = list()
            cba["info"]["functions"].extend(parent_cba["info"]["functions"])
        if "materials" in parent_cba["info"]:
            if "materials" not in cba["info"]:
                cba["info"]["materials"] = parent_cba["info"]["materials"]
            else:
                if cba["info"]["materials"]["policy"] == parent_cba["info"]["materials"]["policy"]:
                    cba["info"]["materials"]["list"].extend(
                        parent_cba["info"]["materials"]["list"])
                elif cba["info"]["materials"]["policy"] == "disallow":
                    m = parent_cba["info"]["materials"]["list"]
                    for i in cba["info"]["materials"]["list"]:
                        for j in m:
                            if i == j:
                                m.remove(j)
                                break
                    cba["info"]["materials"]["list"] = m

    except KeyError as ke:
        raise ke

    return cba
