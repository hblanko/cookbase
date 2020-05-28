from typing import Any, Dict

from cookbase.db import handler


def unroll(cba: Dict[str, Any]) -> Dict[str, Any]:
    """Returns an augmented :ref:`Cookbase Appliance (CBA) <cba>` by retrieving its
    parent CBAs recursively.

    If the :ref:`CBA <cba>` has a parent, :func:`unroll` is recursively called returning
    an augmented structure with inherited data on :code:`functions`, :code:`materials`,
    and the :code:`id` field updated to a list that include all the parent
    :code:`id`\ s; if the CBA has no parents, it is returned with no modifications.

    :param cba: A :ref:`CBA <cba>` to be unrolled
    :type cba: dict[str, Any]
    :return: An augmented :ref:`CBA <cba>`
    :rtype: dict[str, Any]

    :raises KeyError: An attempt on accessing a key in the provided or any parent
      :ref:`CBA <cba>` failed
    """
    try:
        if cba["info"]["familyLevel"] <= 1:
            return cba

        parent_cba = handler.get_handler().get_cba(cba["info"]["parent"])

        if parent_cba["info"]["familyLevel"] > 1:
            parent_cba = unroll(parent_cba)

        if isinstance(parent_cba["id"], list):
            aggregated_id = parent_cba["id"] + [cba["id"]]
        else:
            aggregated_id = [parent_cba["id"], cba["id"]]

        cba["id"] = aggregated_id

        if "functions" in parent_cba["info"]:
            if "functions" not in cba["info"]:
                cba["info"]["functions"] = []

            cba["info"]["functions"].extend(parent_cba["info"]["functions"])

        if "materials" in parent_cba["info"]:
            if "materials" not in cba["info"]:
                cba["info"]["materials"] = parent_cba["info"]["materials"]
            else:
                if (
                    cba["info"]["materials"]["policy"]
                    == parent_cba["info"]["materials"]["policy"]
                ):
                    cba["info"]["materials"]["list"].extend(
                        parent_cba["info"]["materials"]["list"]
                    )
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
