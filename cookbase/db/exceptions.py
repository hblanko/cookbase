from bson import ObjectId


class DBHandlerException(Exception):
    """Base class for :mod:`cookbase.db.handler` errors."""

    db_handler_class_name = "cookbase.db.handler.DBHandler"


class DBClientConnectionError(DBHandlerException):
    """Raised when trying to access a database results in a connection error.

    :ivar str db_id: The database id

    """

    def __init__(self, db_id: str):
        self.db_id = db_id

    def __str__(self):
        return f"Connection failure with database '{self.db_id}'."


class DBNotRegisteredError(DBHandlerException):
    """Raised when trying to access a non-registered database.

    :ivar str db_id: The database identifier

    """

    def __init__(self, db_id: str):
        self.db_id = db_id

    def __str__(self):
        return (
            f"There is no '{self.db_id}' database registered on "
            f"{self.db_handler_class_name}."
        )


class InsertionError(DBHandlerException):
    """Base class for exceptions raised when an insertion operation resulted
    unsuccessful.

    """

    def __init__(self):
        pass


class CBRInsertionError(InsertionError):
    """Raised when a CBR insertion resulted unsuccessful.

    """

    def __init__(self, partial_result):
        self.partial_result = partial_result

    def __str__(self):
        return "Storing CBR in database failed"


class CBRGraphInsertionError(InsertionError):
    """Raised when a CBRGraph insertion resulted unsuccessful.

    """

    def __init__(self, partial_result):
        self.partial_result = partial_result

    def __str__(self):
        return "Storing CBRGraph in database failed"


class InvalidDBTypeError(DBHandlerException):
    """Raised when trying to use an invalid database type.

    :ivar str invalid_db_type: The invalid database type

    """

    def __init__(self, invalid_db_type: str):
        self.invalid_db_type = invalid_db_type

    def __str__(self):
        return f"'{self.invalid_db_type}' is not a valid database type."
