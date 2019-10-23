from typing import Set


class CbrValidationError(Exception):
    '''Base class for validation errors.'''
    pass


class InstrumentNotAvailableError(CbrValidationError):
    '''Raised when trying to use an unavailable instrument.

    :ivar str instrument: Instrument identifier
    :ivar str process: Process identifier
    '''

    def __init__(self,
                 instrument: str,
                 process: str):
        self.instrument = instrument
        self.process = process

    def __str__(self):
        return "Instrument '" + self.instrument + "' is not available for the process'" + self.process + "'"


class NecessaryInstrumentsError(CbrValidationError):
    '''Raised when the conditions of necessary instruments are not met.

    :ivar str process: Process identifier
    '''

    def __init__(self,
                 process: str):
        self.process = process

    def __str__(self):
        return "Definition requirements of necessary instruments sets not met for process '" + self.process + "'"


class NoInstrumentUsedAfterError(CbrValidationError):
    '''Raised when there is no instrument remaining used after a given process.

    :ivar str process: Process identifier
    '''

    def __init__(self,
                 process: str):
        self.process = process

    def __str__(self):
        return "No instrument remains used after process '" + self.process + "'"


class PreparationFlowError(CbrValidationError):
    '''Raised when the recipe does not fulfill preparation flow requirements.'''

    def __str__(self):
        return "Preparation does not meet flow requirements"


class PreparationKeyError(CbrValidationError):
    '''Raised when an identifier is not found in the JSON document.

    :ivar str key: The identifier attempted to access
    '''

    def __init__(self,
                 key: str):
        self.key = key

    def __str__(self):
        return "Bad identifier " + self.key


class IngredientsNotUsedError(CbrValidationError):
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
