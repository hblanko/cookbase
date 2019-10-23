from typing import Any

import networkx as nx
from networkx.readwrite import json_graph
import json


class RecipeGraph():
    '''Class building and storing a recipe graph from recipes based on the Cookbase Recipe Format.

    It makes use of the `networkx` library to generate the graph.
    
    :ivar _used_instruments: The set of instruments being used at a given state of the graph
    :vartype _used_instruments: set[str]
    :ivar _g: The set of instruments being used at a given state of the graph
    :vartype _g: networkx.classes.digraph.DiGraph
    '''

    def __init__(self):
        '''Constructor method'''
        self._used_instruments = set()
        self._g = nx.DiGraph()

    def add_foodstuff(self,
                      foodstuff_id: str,
                      process_id: str = None) -> Any:
        '''Adds a foodstuff and its corresponding edges to the recipe graph

        :param str foodstuff_id: Foodstuff identifier
        :param str process_id: Identifier for the process which the added foodstuff merges into, defaults to `None`
        :type process_id: str, optional
        '''
        if process_id == None:
            self._g.add_node(foodstuff_id)
        else:
            self._g.add_edge(foodstuff_id, process_id)

    def add_instrument(self,
                       instrument_id: str,
                       process_id: str,
                       used_after: bool = False) -> None:
        '''Adds an instrument and its corresponding edges to the recipe graph

        :param str instrument_id: Instrument identifier
        :param str process_id: Process identifier
        :param bool used_after: A flag indicating whether the given instrument remains used after finishing the given process (`True`) or not (`False`), defaults to `False`
        '''
        if instrument_id not in self._used_instruments:
            self._g.add_edge(instrument_id + ":" + process_id, process_id)
            if used_after == True:
                self._used_instruments.add(instrument_id)
            else:
                self._g.add_edge(process_id, instrument_id + ":" + process_id)
                
        elif used_after == False:
            self._g.add_edge(process_id, instrument_id + ":" + process_id)
            self._used_instruments.remove(instrument_id)

    def output(self,
               output_path: str) -> None:
        '''Generates the output in SVG file format

        :param str output_path: Path where output files are to be located
        '''
#         self.g.add_node("ing1", api="LINK")
#         nx.draw(self.g, pos=nx.spring_layout(self.g))
#         nx.write_graphml(self.g, output_path + "/recipe.xml", prettyprint=True)
#         plt.show()
        with open(output_path + "/recipe.json", "w") as f:
            f.write(json.dumps(json_graph.node_link_data(self._g), indent = 2))
