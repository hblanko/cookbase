import requests


class Definitions():
    """Class that provides global definitions for the Cookbase Platform.

    :ivar str schema_base_url: The base url to the JSON Schema defining the Cookbase Recipe Format
    :ivar str definitions_url: The url to the JSON Schema defining Cookbase Recipe Format global definitions
    :ivar str cbr_schema_url: The url to the JSON Schema defining the Cookbase Recipe Format
    :ivar materials: The list of appliance materials
    :vartype materials: list[str]
    :ivar appliance_functions: The list of appliance functions
    :vartype appliance_functions: list[str]
    :ivar foodstuff_keywords: The list of foodstuff keywords available for CBPs
    :vartype foodstuff_keywords: list[str]
    """
    schema_base_url = "http://www.landarltracker.com/schemas"
    definitions_url = schema_base_url + "/cb-global-definitions.json"
    cbr_schema_url = schema_base_url + "/cbr.json"
    materials = None
    appliance_functions = None
    foodstuff_keywords = None

    @staticmethod
    def _setup() -> None:
        """Sets the variables by reading the global definitions document of the Cookbase Recipe Format"""
        d = requests.get(Definitions.definitions_url).json()
        Definitions.materials = d["material"]["enum"]
        Definitions.appliance_functions = d["applianceFunction"]["enum"]
        Definitions.foodstuff_keywords = d["foodstuffKeywords"]["enum"]


Definitions._setup()
