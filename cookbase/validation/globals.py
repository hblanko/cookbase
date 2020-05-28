import requests


class Definitions:
    """Class that provides global definitions for the Cookbase platform.

    :ivar str schema_base_url: The base URL to the :doc:`Cookbase Data Model (CBDM)
      <cbdm>` Schemas
    :ivar str definitions_url: The URL to the :doc:`CBDM <cbdm>` common definitions
      document
    :ivar str cbr_schema_url: The URL to the :ref:`Cookbase Recipe (CBR) <cbr>` Schema
    :ivar materials: The list of :ref:`Cookbase Appliance (CBA) <cba>` materials
    :vartype materials: list[str]
    :ivar appliance_functions: The list of :ref:`CBA <cba>` functions
    :vartype appliance_functions: list[str]
    :ivar foodstuff_keywords: The list of :ref:`Cookbase Process (CBP) <cbp>`
      foodstuff keywords
    :vartype foodstuff_keywords: list[str]
    """

    schema_base_url = "http://landarltracker.com/schemas"
    definitions_url = f"{schema_base_url}/cb-common-definitions.json"
    cbr_schema_url = f"{schema_base_url}/cbr/cbr.json"
    materials = None
    appliance_functions = None
    foodstuff_keywords = None

    @staticmethod
    def _setup() -> None:
        """Sets the variables by reading the :doc:`Cookbase Data Model (CBDM) <cbdm>`
        common definitions document.
        """
        d = requests.get(Definitions.definitions_url).json()
        Definitions.materials = d["$defs"]["material"]["enum"]
        Definitions.appliance_functions = d["$defs"]["applianceFunction"]["enum"]
        Definitions.foodstuff_keywords = d["$defs"]["foodstuffKeywords"]["enum"]


Definitions._setup()
