from typing import Set


class CBRValidationException(Exception):
    '''Base class for CBRvalidation errors.'''
    pass


class ApplianceNotAvailableError(CBRValidationException):
    '''Raised when trying to use an unavailable appliance.

    :ivar str appliance: Appliance identifier
    :ivar str process: Process identifier
    '''

    def __init__(self,
                 appliance: str,
                 process: str):
        self.appliance = appliance
        self.process = process

    def __str__(self):
        return "Appliance '" + self.appliance + \
            "' is not available for the process'" + self.process + "'"


class NecessaryAppliancesError(CBRValidationException):
    '''Raised when the conditions of necessary appliances are not met.

    :ivar str process: Process identifier
    '''

    def __init__(self,
                 process: str):
        self.process = process

    def __str__(self):
        return "Definition requirements of necessary appliances sets not met for process '" + \
            self.process + "'"


class NoApplianceUsedAfterError(CBRValidationException):
    '''Raised when there is no appliance remaining used after a given process.

    :ivar str process: Process identifier
    '''

    def __init__(self,
                 process: str):
        self.process = process

    def __str__(self):
        return "No appliance remains used after process '" + self.process + "'"


class PreparationFlowError(CBRValidationException):
    '''Raised when the recipe does not fulfill preparation flow requirements.'''

    def __str__(self):
        return "Preparation does not meet flow requirements"


class PreparationKeyError(CBRValidationException):
    '''Raised when an identifier is not found in the JSON document.

    :ivar str key: The identifier attempted to access
    '''

    def __init__(self,
                 key: str):
        self.key = key

    def __str__(self):
        return "Bad identifier " + self.key


class IngredientsNotUsedError(CBRValidationException):
    '''Raised when remaining ingredients are found after end of preparation flow.

    :ivar foodstuffs: A set of ingredient identifiers
    :vartype foodstuffs: set[str]
    '''

    def __init__(self,
                 foodstuffs: Set[str]):
        self.foodstuffs = foodstuffs

    def __str__(self):
        s = str()
        for i in self.foodstuffs:
            if i.startswith("ing"):
                if s != "":
                    s += " ,"
                s += "'" + i + "'"
        return "Ingredient/s " + s + " not used"


class StorageError(CBRValidationException):
    '''Raised when there was an error storing the recipe and/or the graph in the database.
    '''

    def __init__(self):
        pass

    def __str__(self):
        return "Error storing the recipe and/or the graph in the database"
