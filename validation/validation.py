import sys
from typing import Any, Dict, Tuple

import jsonschema

from cookbase.graph.recipegraph import RecipeGraph
from cookbase.validation.exceptions import (IngredientsNotUsedError,
                                            InstrumentNotAvailableError,
                                            NecessaryInstrumentsError,
                                            NoInstrumentUsedAfterError,
                                            PreparationFlowError,
                                            PreparationKeyError)


class Validation():
    '''Class performing validation and graph construction of recipes in JSON Cookbase Format.

    :ivar str _schema_base_uri: The base uri to the JSON Schema directory for the JSON Cookbase Format
    :ivar _foodstuffs: A structure storing data of remaining foodstuffs in preparation flow
    :vartype _foodstuffs: dict[str, dict[str, Any]]
    :ivar _instruments: A structure storing data of involved instruments together with a string containing the identifier of the process using the instrument
    :vartype _instruments: dict[str, tuple[dict[str, Any], str]]
    :ivar _schema_ref_resolver: An instance of :class:`jsonschema.validators.RefResolver` resolving remote references to JSON Schemas
    :vartype _schema_ref_resolver: jsonschema.validators.RefResolver
    :ivar _rg: An instance of :class:`cookbase.graph.RecipeGraph` storing the recipe graph information, defaults to `None`
    :vartype _rg: cookbase.graph.recipegraph.RecipeGraph, optional
    '''

    def __init__(self,
                 schema_base_uri: str,
                 rg: RecipeGraph = None):
        '''Constructor method'''
        self._schema_base_uri = schema_base_uri
        self._schema_ref_resolver = jsonschema.validators.RefResolver.from_schema({"$ref": self._schema_base_uri + "/recipe.json"})
        self._rg = rg

    def _update_foodstuffs(self,
                          process_id: str,
                          process_foodstuffs: Tuple[str, ...]) -> None:
        '''Updates internal ``_foodstuffs`` structure given the process information and adds foodstuffs to recipe graph

        :param str process_id: Process identifier
        :param process_foodstuffs: Array of foodstuffs identifiers involved in the given process
        :type process_foodstuffs: tuple[str, ...]
        '''
        if self._rg is not None:
            v = self._rg.add_foodstuff(process_id)
        for i in process_foodstuffs:
            if self._rg is not None:
                self._rg.add_foodstuff(i, v)
            del self._foodstuffs[i]
        self._foodstuffs[process_id] = None

    def _validate_instruments_usage(self,
                                   process_id: str,
                                   process: Dict[str, Any],
                                   process_foodstuffs: Tuple[str, ...],
                                   necessary_instruments: Tuple[Tuple[Tuple[str, str], ...], ...]) -> None:
        '''Validates the usage of a given instrument in the preparation flow and adds instruments to recipe graph

        :param str process_id: Process identifier
        :param process: The JSON document representing the process to be validated
        :type process: dict[str, Any]
        :param process_foodstuffs: Array of foodstuffs identifiers involved in the given process
        :type process_foodstuffs: tuple[str, ...]
        :param necessary_instruments: A CNF formula conditioning the possible sets of necessary instruments for the given process
        :type necessary_instruments: tuple[tuple[tuple[str, str], ...], ...]
        :raises: :class:`cookbase.validation.InstrumentNotAvailableError`: An ingredient is not available for the given process
        :raises: :class:`cookbase.validation.NecessaryInstrumentsError`: Requirements of mandatory instruments not met for the given process
        :raises: :class:`cookbase.validation.NoInstrumentUsedAfterError`: No instrument remains used after given process
        '''
        necessary_insts_flag = False
        one_used_after = False
        count = 0

        # Checking conditions on instruments for each process
        for i in process["instruments"]:
            if self._instruments[i["instrument"]][1] != None and self._instruments[i["instrument"]][1] not in process_foodstuffs:
                raise InstrumentNotAvailableError(i["instrument"], process_id)
            for a in necessary_instruments:
                for b in a:
                    if b[0] in self._instruments[i["instrument"]][0] and self._instruments[i["instrument"]][0][b[0]] == b[1]:
                        count += 1
                if count == len(a):
                    necessary_insts_flag = True
                    break
            if i["usedAfter"] == True:
                one_used_after = True
                self._instruments[i["instrument"]][1] = process_id
                if self._rg is not None:
                    self._rg.add_instrument(i["instrument"], process_id, True)
            else:
                self._instruments[i["instrument"]][1] = None
                if self._rg is not None:
                    self._rg.add_instrument(i["instrument"], process_id, False)

        if necessary_insts_flag == False:
            raise NecessaryInstrumentsError(process_id)
        if one_used_after == False:
            raise NoInstrumentUsedAfterError(process_id)

    def _validate_process(self,
                         process_id: str,
                         process: Dict[str, Any]) -> None:
        '''Performs validation of a given process in the preparation flow

        :param str process_id: Process identifier
        :param process: The JSON document representing the process to be validated
        :type process: dict[str, Any]
        '''
        splits = process["process"].split(' ')
        schema_basename = splits[0] + "".join(x.title() for x in splits[1:]) + ".json"
        process_definitions = self._schema_ref_resolver.resolve_from_url(self._schema_base_uri +
                                                                         "/process/" +
                                                                         schema_basename +
                                                                         "#/definitions")

        # Building involved foodstuffs array
        process_foodstuffs = list()
        fk = list()
        a = process_definitions["foodstuffKeywords"]
        if isinstance(a, str):
            fk.append(a)
        elif isinstance(a, list):
            fk = a
        if len(fk) == 1:
            b = process[fk[0]]
            if isinstance(b, list):
                process_foodstuffs = b
            elif isinstance(b, str):
                process_foodstuffs.append(b)
        else:
            for i in fk:
                b = process[i]
                if isinstance(b, str):
                    process_foodstuffs.append(b)
                elif isinstance(b, list):
                    for j in b:
                        process_foodstuffs.append(j)

        # Building CNF formula for necessary instruments
        necessary_instruments = list(tuple(tuple()))
        a = process_definitions["conditions"]["necessaryInstruments"]
        b = list(tuple())
        if isinstance(a, list):
            if len(a) == 1:
                for v in a[0].values():
                    b.append((v[0], v[1]))
                necessary_instruments.append((*b,))
            else:
                for i in a:
                    b = list(tuple())
                    for v in i.values():
                        b.append((v[0], v[1]))
                    necessary_instruments.append((*b,))
        elif isinstance(a, dict):
            for v in a.values():
                b.append((v[0], v[1]))
            necessary_instruments.append((*b,))

        # Updating internal structure of preparation foodstuffs
        self._update_foodstuffs(process_id, (*process_foodstuffs,))
        self._validate_instruments_usage(process_id, process, (*process_foodstuffs,), (*necessary_instruments,))

    def validate_preparation(self,
                             data: Dict[str, Any]) -> None:
        '''Performs validation of preparation flow and builds recipe graph

        :param data: The JSON document representing the recipe to be validated
        :type data: dict[str, Any]
        :raises: :class:`cookbase.validation.IngredientsNotUsedError`: One or more ingredients are not used for the preparation
        :raises: :class:`cookbase.validation.PreparationFlowError`: Preparation does not meet flow requirements
        :raises: :class:`cookbase.validation.PreparationKeyError`: Bad process/ingredient/instrument identifier
        '''
        try:
            # Building internal structures from parsed JSON document
            for i in data["ingredients"].keys():
                for k, v in data["ingredients"][i].items():
                    if k != "name":
                        self._foodstuffs[k] = v
            for i in data["instruments"].keys():
                self._instruments[i] = [data["instruments"][i], None]

            # Iterating over preparation processes to validate
            for i in range(1, len(data["preparation"]) + 1):
                process = data["preparation"]["proc" + str(i)]
                self._validate_process("proc" + str(i), process)

            # Checking consistency of preparation flow
            for i in self._foodstuffs.keys():
                if i.startswith("ing"):
                    raise IngredientsNotUsedError(self._foodstuffs.keys())
            if len(self._foodstuffs) != 1 or "proc" + str(len(data["preparation"])) not in self._foodstuffs.keys():
                raise PreparationFlowError
        except KeyError as ke:
            tb = sys.exc_info()[2]
            raise PreparationKeyError(str(ke)).with_traceback(tb) from None

    def validate_recipe(self,
                        data: Dict[str, Any]) -> None:
        '''Performs validation of recipe format and graph construction
        
        The validation process is implemented in two stages: firstly, a JSON Schema validation is performed, 
        and secondly the preparation process is checked for consistency regarding the available ingredients, 
        instruments and the preparation flow conditions and constraints, while building the recipe graph.

        :param data: The JSON document representing the recipe to be validated
        :type data: dict[str, Any]
        '''
        schema = {"$ref": self._schema_base_uri + "/recipe.json"}
        jsonschema.validate(data, schema)
        self._foodstuffs = dict()
        self._instruments = dict()
        self.validate_preparation(data)

    def graph_output(self,
                     output_path: str) -> None:
        '''Generates graph output in SVG file format

        :param str output_path: Path where graph output files are to be located
        '''
        self._rg.output(output_path)
