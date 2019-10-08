from typing import Any, Dict

from graph_tool import Graph, Vertex
from graph_tool.draw.cairo_draw import graph_draw


class RecipeGraph(Graph):
    '''Class building and storing a recipe graph from recipes based on the JSON Cookbase Format.

    It uses the `graph-tool` module, inheriting the class :class:`graph_tool.Graph`.
    
    :ivar __data: The recipe document in JSON Cookbase Format
    :vartype __data: dict[str, Any]
    :ivar __process_vertices: An index of graph vertices that represent processes, stored by process identifier
    :vartype __process_vertices: dict[str, graph_tool.Vertex]
    :ivar __used_instruments: The set of instruments being used at a given state of the graph
    :vartype __used_instruments: set[str]
    :ivar __vertex_properties: An instance of :class:`graph_tool.PropertyMap` storing the ingredients, instruments and processes identifiers
    :vartype __vertex_properties: graph_tool.PropertyMap
    :ivar __vertex_properties_c: An instance of :class:`graph_tool.PropertyMap` storing the colors for the graph vertices
    :vartype __vertex_properties_c: graph_tool.PropertyMap
    '''

    def __init__(self,
                 data: Dict[str, Any]):
        '''Constructor method'''
        super(RecipeGraph, self).__init__()
        self.__data = data 
        self.__process_vertices = dict()
        self.__used_instruments = set()
        self.__vertex_properties = self.new_vertex_property("string")
        self.__vertex_properties_c = self.new_vertex_property("string")

    def add_foodstuff(self,
                      foodstuff_id: str,
                      process_vertex: Vertex = None) -> Any:
        '''Adds a foodstuff and its corresponding edges to the recipe graph

        :param str foodstuff_id: Foodstuff identifier
        :param process_vertex: The vertex representing the process which the added foodstuff merges into, defaults to `None`
        :type process_vertex: graph_tool.Vertex, optional
        '''
        if process_vertex == None:
            v = self.add_vertex()
            self.__vertex_properties[v] = foodstuff_id
#             self.vertex_properties[v] = self.__data["preparation"][foodstuff_id]["process"]
            if (len(self.__process_vertices) == 0):
                self.__vertex_properties_c[v] = "#99cc00"
            else:
                self.__vertex_properties_c[v] = "#a40000"
            self.__process_vertices[foodstuff_id] = v
            return v
        else:
            if foodstuff_id.startswith("ing"):
                v = self.add_vertex()
                self.__vertex_properties[v] = foodstuff_id
                self.__vertex_properties_c[v] = "#ff6600"
                self.add_edge(v, process_vertex)
            elif foodstuff_id.startswith("proc"):
                self.add_edge(self.__process_vertices[foodstuff_id], process_vertex)

    def add_instrument(self,
                       instrument_id: str,
                       process_id: str,
                       used_after: bool = False) -> None:
        '''Adds an instrument and its corresponding edges to the recipe graph

        :param str instrument_id: Instrument identifier
        :param str process_id: Process identifier
        :param bool used_after: A flag indicating whether the given instrument remains used after finishing the given process (`True`) or not (`False`), defaults to `False`
        '''
        if instrument_id not in self.__used_instruments:
            v = self.add_vertex()
            self.__vertex_properties[v] = instrument_id
            self.__vertex_properties_c[v] = "#3366ff"
            self.add_edge(v, self.__process_vertices[process_id])
            if used_after == True:
                self.__used_instruments.add(instrument_id)
            else:
                self.add_edge(self.__process_vertices[process_id], v)
        elif used_after == False:
            v = self.add_vertex()
            self.__vertex_properties[v] = instrument_id
            self.__vertex_properties_c[v] = "#3366ff"
            self.add_edge(self.__process_vertices[process_id], v)
            self.__used_instruments.remove(instrument_id)

    def output(self,
               output_path: str) -> None:
        '''Generates the output in SVG file format

        :param str output_path: Path where output files are to be located
        '''
        self.vertex_properties["id"] = self.__vertex_properties
        self.vertex_properties["fill_color"] = self.__vertex_properties_c
#         self.save(output_path + "/recipe.xml", "graphml")
        graph_draw(self, vertex_text=self.vertex_properties["id"], vertex_fill_color=self.vertex_properties["fill_color"], vertex_font_size=11, vertex_size=20, output=output_path + "/recipe.svg", output_size=(2200,1500))
