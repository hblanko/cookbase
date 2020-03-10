class DBHandlerException(Exception):
    '''Base class for :class:`cookbase.db.handler.DBHandler` errors.'''
    db_handler_class_name = 'cookbase.db.handler.DBHandler'


class DBTypeError(DBHandlerException):
    '''Raised when trying to access a database with wrong type.

    :ivar str db_type: Database type

    '''

    def __init__(self, db_type: str):
        self.db_type = db_type

    def __str__(self):
        return '"' + self.db_type + '" is not a database type implemented by ' + \
            self.db_handler_class_name + '.'


class DBNotRegisteredError(DBHandlerException):
    '''Raised when trying to access a non-registered database.

    :ivar str db_id: Database identifier

    '''

    def __init__(self,
                 db_id: str):
        self.db_id = db_id

    def __str__(self):
        return 'There is no "' + self.db_id + '" database registered on ' + \
            self.db_handler_class_name + '.'
