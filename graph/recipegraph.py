from typing import Any, Dict, Hashable, List

import networkx as nx
from networkx.readwrite import json_graph

from cookbase.validation.globals import Definitions
from cookbase.validation.logger import logger


class RecipeGraph():
    """Class building and analyzing a recipe graph (CBR-Graph) from recipes based on the Cookbase Recipe Format.

    It makes use of the :mod:`networkx` library to generate the graph.

    :ivar g: An instance of a :mod:`networkx` directed graph
    :vartype g: networkx.classes.digraph.DiGraph
    :ivar _appliances: A dictionary of appliance references included in the recipe
    :vartype _appliances: dict[str]
    :ivar _pending_processes_edges: A list of 2-tuples denoting the edges pending to be added
    :vartype _pending_processes_edges: list[tuple[str, str]]
    """
    g = nx.DiGraph()
    _appliances = dict()
    _pending_processes_edges = list()

    def __init__(self):
        '''Constructor method'''
        pass

    def add_ingredient(self,
                       ingredient_ref: str,
                       ingredient: Dict[str, Any]) -> None:
        """Adds an ingredient to the graph

        :param str ingredient_ref: Ingredient reference
        :param ingredient: Ingredient object as extracted from a CBR
        :type ingredient: dict[str, Any]
        """
        self.g.add_node(ingredient_ref, type="cbi", cbiId=ingredient["cbiId"])

    def add_appliance(self,
                      appliance_ref: str,
                      appliance: Dict[str, Any]) -> None:
        """Adds an appliance to the graph

        :param str appliance_ref: Appliance reference
        :param appliance: Appliance object as extracted from a CBR
        :type appliance: dict[str, Any]
        """
        if "cbaId" in appliance:
            a = {"type": "cba", "cbaId": appliance["cbaId"]}
        else:
            a = {"type": "cba-virtual"}
        self._appliances[appliance_ref] = a
#         self.g.add_node(appliance_ref, type="cba", cbaId=appliance["cbaId"])

    def add_process(self,
                    process_ref: str,
                    process: Dict[str, Any]) -> None:
        """Adds a process and its in-edges to the graph

        :param str process_ref: Process reference
        :param process: Process object as extracted from a CBR
        :type process: dict[str, Any]
        """
        self.g.add_node(process_ref, type="cbp", cbpId=process["cbpId"])

        def add_foodstuff_edge(foodstuff_ref, process_ref):
            if foodstuff_ref in self.get_ingredients() or foodstuff_ref in self.get_processes():
                self.g.add_edge(foodstuff_ref, process_ref)
            else:
                self._pending_processes_edges.append(
                    (foodstuff_ref, process_ref))

        # Adding foodstuff edges
        for fk in Definitions.foodstuff_keywords:
            if fk in process.keys():
                if isinstance(process[fk], str):
                    add_foodstuff_edge(process[fk], process_ref)
                else:
                    for i in process[fk]:
                        add_foodstuff_edge(i, process_ref)

        # TODO: Solve adding appliance edges
        self.g.add_node(process_ref, appliances=process["appliances"])

    def resolve_pending_processes_edges(self) -> None:
        """Attempts to add edges that could not have been added before"""
        not_found = list()
        for i in range(len(self._pending_processes_edges)):
            in_process, out_process = self._pending_processes_edges[i]
            if in_process in self.get_processes():
                self.g.add_edge(in_process, out_process)
            else:
                not_found.append(self._pending_processes_edges[i])
        self._pending_processes_edges = not_found

    def clear(self) -> None:
        """Clears graph and internal structures"""
        self.g.clear()
        self._appliances.clear()
        self._pending_processes_edges.clear()

    def build_graph(self, data: Dict[str, Any]) -> None:
        """Adds a process and its in-edges to the graph

        :param data: A dictionary containing all the data from a CBR
        :type data: dict[str, Any]
        """
        self.clear()
        self.g.graph["name"] = data["info"]["name"]
        for k, v in data["ingredients"].items():
            self.add_ingredient(k, v)
        for k, v in data["appliances"].items():
            self.add_appliance(k, v)
        for k, v in data["preparation"].items():
            self.add_process(k, v)
        self.resolve_pending_processes_edges()
        for in_foodstuff, out_process in self._pending_processes_edges:
            self.g.add_node(in_foodstuff, type="unref_foodstuff")
            self.g.add_edge(in_foodstuff, out_process)
            logger.error(
                "Neither ingredient nor process found with reference '" +
                in_foodstuff + "'")

    def processes_subgraph(self) -> nx.DiGraph:
        """Returns the subgraph of the CBR-Graph including only the processes

        :return: The processes subgraph from the CBR-Graph
        :rtype: networkx.classes.digraph.DiGraph
        """
        nodes = list()
        for node, _ in self.g.nodes(data="type"):
            if _ == "cbp":
                nodes.append(node)
        return self.g.subgraph(nodes)

    def get_ingredients(self) -> List[Hashable]:
        """Returns the list of nodes representing ingredients in the CBR-Graph

        :return: The list of ingredient nodes from the CBR-Graph
        :rtype: list[Hashable]
        """
        return [i for i, _ in self.g.nodes(data="type") if _ == "cbi"]

    def get_processes(self) -> List[Hashable]:
        """Returns the list of nodes representing processes in the CBR-Graph

        :return: The list of process nodes from the CBR-Graph
        :rtype: list[Hashable]
        """
        return [i for i, _ in self.g.nodes(data="type") if _ == "cbp"]

    def get_root_processes(self) -> List[Hashable]:
        """Returns the list of root nodes from the processes subgraph

        :return: The list of process root nodes from the processes subgraph
        :rtype: list[Hashable]
        """
        return [i for i, _ in self.processes_subgraph().in_degree()
                if _ == 0]

    def get_merging_processes(self) -> List[Hashable]:
        """Returns the list of nodes in which the processes subgraph merges two or more process flows or branches

        :return: The list of merging process nodes from the processes subgraph
        :rtype: list[Hashable]
        """
        return [i for i, _ in self.processes_subgraph().in_degree()
                if _ > 1]

    def get_leaf_processes(self) -> List[Hashable]:
        """Returns the list of leaf nodes from the processes subgraph

        :return: The list of process leaf nodes from the processes subgraph
        :rtype: list[Hashable]
        """
        return [i for i, _ in self.processes_subgraph().out_degree()
                if _ == 0]

    def get_serializable_graph(self) -> Dict[str, Any]:
        """Returns CBR-Graph data in a JSON-serializable format

        :return: A dict with the CBR-Graph data
        :rtype: dict[str, Any]
        """
        return json_graph.node_link_data(self.g)
