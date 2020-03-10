from typing import Any, Dict, Hashable, List

import networkx as nx
from networkx.readwrite import json_graph

from cookbase.validation.globals import Definitions
from cookbase.validation.logger import logger


class RecipeGraph():
    '''A class that provides the structures and methods needed to build, manipulate and
    analyze :doc:`Cookbase Recipe Graphs (CBRGraphs) <cbrg>`.

    Typically, a :doc:`CBRGraph <cbrg>` is generated by extracting the data from a
    complete traversal of a :ref:`Cookbase Recipe (CBR) <cbr>`. It makes use of the
    `NetworkX <https://networkx.github.io/>`_ graph manipulation package.

    :ivar g: An instance of a :mod:`networkx` directed graph
    :vartype g: networkx.classes.digraph.DiGraph
    :ivar _appliances: A dictionary of appliance references included in the recipe
    :vartype _appliances: dict[str]
    :ivar _pending_processes_edges: A list of 2-tuples denoting the edges pending to be
      added
    :vartype _pending_processes_edges: list[tuple[str, str]]

    '''
    g = nx.DiGraph()
    _appliances = {}
    _pending_processes_edges = []

    def __init__(self):
        '''Constructor method.'''
        pass

    def add_ingredient(self, ingredient_ref: str, ingredient: Dict[str, Any]) -> None:
        '''Adds an ingredient to the graph.

        :param str ingredient_ref: A :ref:`CBR Ingredient <cbr-ingredients>` reference
        :param ingredient: Dictionary representing a
          :ref:`CBR Ingredient <cbr-ingredients>`
        :type ingredient: dict[str, Any]
        '''
        self.g.add_node(ingredient_ref, type='cbi', cbiId=ingredient['cbiId'])

    def add_appliance(self, appliance_ref: str, appliance: Dict[str, Any]) -> None:
        '''Adds an appliance to the graph.

        :param str appliance_ref: A :ref:`CBR Appliance <cbr-appliances>` reference
        :param appliance: Dictionary representing a
          :ref:`CBR Appliance <cbr-appliances>`
        :type appliance: dict[str, Any]
        '''
        if 'cbaId' in appliance:
            a = {'type': 'cba', 'cbaId': appliance['cbaId']}
        else:
            a = {'type': 'cba-virtual'}

        self._appliances[appliance_ref] = a
#         self.g.add_node(appliance_ref, type='cba', cbaId=appliance['cbaId'])

    def add_process(self, process_ref: str, process: Dict[str, Any]) -> None:
        '''Adds a process and its in-edges to the graph.

        :param str process_ref: A :ref:`CBR Process <cbr-preparation>` reference
        :param process: Dictionary representing a
          :ref:`CBR Process <cbr-preparation>`
        :type process: dict[str, Any]
        '''
        # Building appliances dictionary
        a = {}

        for app in process['appliances']:
            app_ref = app['appliance']
            a[app_ref] = self._appliances[app_ref]
            a[app_ref]['usedAfter'] = app['usedAfter']

        self.g.add_node(process_ref, type='cbp', cbpId=process['cbpId'], appliances=a)

        # Adding foodstuff edges
        def add_foodstuff_edge(foodstuff_ref, process_ref):
            if foodstuff_ref in self.get_ingredients() or \
                    foodstuff_ref in self.get_processes():
                self.g.add_edge(foodstuff_ref, process_ref)
            else:
                self._pending_processes_edges.append((foodstuff_ref, process_ref))

        for fk in Definitions.foodstuff_keywords:
            if fk in process.keys():
                if isinstance(process[fk], str):
                    add_foodstuff_edge(process[fk], process_ref)
                else:
                    for i in process[fk]:
                        add_foodstuff_edge(i, process_ref)

    def resolve_pending_processes_edges(self) -> None:
        '''Attempts to add edges that could not have been added to the graph before.'''
        not_found = []
        for i in range(len(self._pending_processes_edges)):
            in_process, out_process = self._pending_processes_edges[i]
            if in_process in self.get_processes():
                self.g.add_edge(in_process, out_process)
            else:
                not_found.append(self._pending_processes_edges[i])
        self._pending_processes_edges = not_found

    def clear(self) -> None:
        '''Clears the graph and internal structures.'''
        self.g.clear()
        self._appliances.clear()
        self._pending_processes_edges.clear()

    def build_graph(self, data: Dict[str, Any]) -> None:
        '''Adds a process and its in-edges to the graph.

        :param data: A dictionary containing all the data from a CBR
        :type data: dict[str, Any]
        '''
        self.clear()
        self.g.graph['name'] = data['info']['name']
        for k, v in data['ingredients'].items():
            self.add_ingredient(k, v)
        for k, v in data['appliances'].items():
            self.add_appliance(k, v)
        for k, v in data['preparation'].items():
            self.add_process(k, v)
        self.resolve_pending_processes_edges()
        for in_foodstuff, out_process in self._pending_processes_edges:
            self.g.add_node(in_foodstuff, type='unref_foodstuff')
            self.g.add_edge(in_foodstuff, out_process)
            logger.error(
                'Neither ingredient nor process found with reference \'' +
                in_foodstuff + '\'')

    def aggregated_appliances_graph(self) -> nx.DiGraph:
        '''Returns a graph where each node represents a concurrent preparation path of a
        :doc:`CBRGraph <cbrg>`, containing an inverted index on the appliances used in
        that path together with the list of processes that used it.

        :return: An aggregated appliances graph
        :rtype: networkx.classes.digraph.DiGraph
        '''
        # TODO: This operation is implemented single-threaded. Consider
        # multi-threading.
        roots = self.get_root_processes()
        pj_processes = self.path_joining_processes()
        leaf_processes = self.get_leaf_processes()
        aggregated_graph = nx.DiGraph()
        # A dictionary with key the ag_id, and value the starting process of a
        # path
        current_ag_leaves = {}
        # A map of the path-starting process reference into the aggregated path
        # id
        first_pg_to_ag = {}

        for i in range(len(roots)):
            aggregated_graph.add_node(i)
            current_ag_leaves[i] = roots[i]
            first_pg_to_ag[roots[i]] = i

        ag_id_counter = len(current_ag_leaves)

        while current_ag_leaves:
            ag_nodes_already_generated = set()
            pg_nodes_to_generate = set()

            for ag_id, p in current_ag_leaves.items():
                appliances = {}
                s = p
                while True:
                    # Build inverted index on appliance for given process path
                    for app_ref in self.g.nodes[s]['appliances'].keys():
                        if app_ref not in appliances:
                            appliances[app_ref] = [s]
                        else:
                            appliances[app_ref].append(s)

                    if s in pj_processes or s in leaf_processes:
                        break
                    # Not path-joining nor leaf: check if path continues
                    t = next(self.g.successors(s))
                    if t in pj_processes:
                        break
                    else:
                        s = t  # Iterate over path

                aggregated_graph.add_node(ag_id, appliances=appliances)
                ag_nodes_already_generated.add(ag_id)

                for v in self.g.successors(s):
                    pg_nodes_to_generate.add((ag_id, v))

            for n in ag_nodes_already_generated:
                del current_ag_leaves[n]
            for ag_id, v in pg_nodes_to_generate:
                if v not in first_pg_to_ag:
                    aggregated_graph.add_edge(ag_id, ag_id_counter)
                    current_ag_leaves[ag_id_counter] = v
                    first_pg_to_ag[v] = ag_id_counter
                    ag_id_counter += 1
                else:
                    aggregated_graph.add_edge(ag_id, first_pg_to_ag[v])

        return aggregated_graph

    def processes_subgraph_view(self) -> nx.DiGraph:
        '''Returns the subgraph view of the :doc:`CBRGraph <cbrg>` including only its
        processes.

        :return: The processes' subgraph view from the :doc:`CBRGraph <cbrg>`
        :rtype: networkx.classes.digraph.DiGraph
        '''
        def filter_process(node):
            return self.g.nodes[node]['type'] == 'cbp'

        return nx.subgraph_view(self.g, filter_node=filter_process)

    def get_ingredients(self) -> List[Hashable]:
        '''Returns the list of nodes representing ingredients in the :doc:`CBRGraph
        <cbrg>`.

        :return: The list of ingredient nodes in the :doc:`CBRGraph <cbrg>`
        :rtype: list[Hashable]
        '''
        return [i for i, _ in self.g.nodes(data='type') if _ == 'cbi']

    def get_processes(self) -> List[Hashable]:
        '''Returns the list of nodes representing processes in the :doc:`CBRGraph
        <cbrg>`.

        :return: The list of process nodes in the :doc:`CBRGraph <cbrg>`
        :rtype: list[Hashable]
        '''
        return [i for i, _ in self.g.nodes(data='type') if _ == 'cbp']

    def get_root_processes(self) -> List[Hashable]:
        '''Returns the list of root nodes from the processes' subgraph.

        :return: The list of process root nodes from the processes' subgraph
        :rtype: list[Hashable]
        '''
        return [i for i, _ in self.processes_subgraph_view().in_degree() if _ == 0]

    def path_joining_processes(self) -> List[Hashable]:
        '''Returns the list of process nodes that represent a junction point
        of two or more preparation paths.

        :return: The list of merging process nodes from the processes' subgraph
        :rtype: list[Hashable]
        '''
        pjp = []
        psw = self.processes_subgraph_view()

        for i in list(psw.nodes):
            if psw.in_degree(i) > 1 or psw.out_degree(i) > 1:
                pjp.append(i)

        return pjp

    def get_leaf_processes(self) -> List[Hashable]:
        '''Returns the list of leaf nodes from the processes' subgraph.

        :return: The list of process leaf nodes from the processes' subgraph.
        :rtype: list[Hashable]
        '''
        return [i for i, _ in self.processes_subgraph_view().out_degree() if _ == 0]

    def get_serializable_graph(self) -> Dict[str, Any]:
        '''Returns the :doc:`CBRGraph <cbrg>` data in a JSON-serializable format.

        :return: A dict with the :doc:`CBRGraph <cbrg>` data
        :rtype: dict[str, Any]
        '''
        return json_graph.node_link_data(self.g)
