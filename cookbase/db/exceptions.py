class DBHandlerException(Exception):
    '''Base class for :class:`cookbase.db.handler.DBHandler` errors.'''
    db_handler_class_name = 'cookbase.db.handler.DBHandler'


class BadCBRGraphError(DBHandlerException):
    '''Raised when the dictionary representing a :doc:`Cookbase Recipe Graph (CBRGraph)
    <cbrg>` is detected not to conform its standard format.

    '''

    def __init__(self):
        pass

    def __str__(self):
        return 'The provided CBRGraph does not conform the standard format.'


class DBClientConnectionError(DBHandlerException):
    '''Raised when trying to access a database results in a connection error.

    :ivar str db_id: The database id

    '''

    def __init__(self, db_id: str):
        self.db_id = db_id

    def __str__(self):
        return f'Connection failure with database \'{self.db_id}\'.'


class DBNotRegisteredError(DBHandlerException):
    '''Raised when trying to access a non-registered database.

    :ivar str db_id: The database identifier

    '''

    def __init__(self,
                 db_id: str):
        self.db_id = db_id

    def __str__(self):
        return (
            f'There is no \'{self.db_id}\' database registered on '
            f'{self.db_handler_class_name}.'
        )


class InvalidDBTypeError(DBHandlerException):
    '''Raised when trying to use an invalid database type.

    :ivar str invalid_db_type: The invalid database type

    '''

    def __init__(self,
                 invalid_db_type: str):
        self.invalid_db_type = invalid_db_type

    def __str__(self):
        return f'\'{self.invalid_db_type}\' is not a valid database type.'
