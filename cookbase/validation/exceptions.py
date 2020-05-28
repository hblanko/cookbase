from typing import Set


class CBRValidationException(Exception):
    """Base class for :ref:`Cookbase Recipe (CBR) <cbr>` validation errors."""

    pass


class ApplianceNotAvailableError(CBRValidationException):
    """Raised when trying to use an unavailable appliance.

    :ivar str appliance: :ref:`CBR Appliance <cbr-appliances>` identifier
    :ivar str process: :ref:`CBR Process <cbr-preparation>` identifier

    """

    def __init__(self, appliance: str, process: str):
        self.appliance = appliance
        self.process = process

    def __str__(self):
        return (
            f"Appliance '{self.appliance}' is not available for the process "
            f"'{self.process}'"
        )


class NecessaryAppliancesError(CBRValidationException):
    """Raised when the conditions of necessary :ref:`CBR Appliances <cbr-appliances>`
    are not met.

    :ivar str process: :ref:`CBR Process <cbr-preparation>` identifier

    """

    def __init__(self, process: str):
        self.process = process

    def __str__(self):
        return (
            "Definition requirements of necessary appliances sets not met for "
            f"process '{self.process}'"
        )


class NoApplianceUsedAfterError(CBRValidationException):
    """Raised when there is no :ref:`CBR Appliance <cbr-appliances>` remaining used
    after a given :ref:`CBR Process <cbr-preparation>`.

    :ivar str process: :ref:`CBR Process <cbr-preparation>` identifier

    """

    def __init__(self, process: str):
        self.process = process

    def __str__(self):
        return f"No appliance remains used after process '{self.process}'"


class PreparationFlowError(CBRValidationException):
    """Raised when the :ref:`CBR <cbr>` does not fulfill the :ref:`preparation flow
    <cbr-preparation>` requirements.

    """

    def __str__(self):
        return "Preparation does not meet flow requirements"


class PreparationKeyError(CBRValidationException):
    """Raised when an identifier is not found in the JSON document.

    :ivar str key: The identifier attempted to access

    """

    def __init__(self, key: str):
        self.key = key

    def __str__(self):
        return f"Bad identifier {self.key}"


class IngredientsNotUsedError(CBRValidationException):
    """Raised when remaining :ref:`CBR Ingredients <cbr-ingredients>` are found after
    end of :ref:`preparation flow <cbr-preparation>`.

    :ivar foodstuffs: A set of :ref:`CBR Ingredient <cbr-ingredients>` identifiers
    :vartype foodstuffs: set[str]

    """

    def __init__(self, foodstuffs: Set[str]):
        self.foodstuffs = foodstuffs

    def __str__(self):
        s = str()

        for i in self.foodstuffs:
            if i.startswith("ing"):
                if s != "":
                    s += " ,"

                s += f"'{i}'"

        return f"Ingredient/s {s} not used"


class StorageError(CBRValidationException):
    """Raised when there was an error storing the :ref:`CBR <cbr>` and/or the
    :doc:`Cookbase Recipe Graph (CBRGraph) <cbrg>` in the database.

    """

    def __init__(self):
        pass

    def __str__(self):
        return "Error storing the recipe and/or the graph in the database"
