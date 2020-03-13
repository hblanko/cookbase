import os
import pathlib
from collections import namedtuple
from typing import Any, Dict, NamedTuple, Optional, Union

import cookbase
import pymongo
from bson.objectid import ObjectId
from cookbase.db.exceptions import (BadCBRGraphError, DBClientConnectionError,
                                    DBNotRegisteredError, InvalidDBTypeError)
from cookbase.db.utils import demongofy


class DBHandler():
    '''A class that handles connections to database instances in order to store and
    retrieve the different :doc:`Cookbase Data Model (CBDM) <cbdm>` elements.

    :param str mongodb_url: A `MongoDB connection URI
      <https://docs.mongodb.com/manual/reference/connection-string/>`_ to use as
      default database
    :param str db_type: An identifier of the database connection to use, defaults to
      :attr:`DBTypes.mongodb`
    :param str db_name: The name of the database to connect to, defaults to
      :const:`'cookbase'`

    :raises DBClientConnectionError: The database connection could not be established
    :raises InvalidDBTypeError: The given database type is not registered as a valid
      database type

    :ivar str _default_db_id: The default database identifier with the form
      :samp:`'{db_type}:{db_name}'`, defaults to :const:`'mongodb:cookbase'`
    :ivar _connections: A dictionary containing the data about all the handled
      connections
    :vartype _connections: dict[str, Any]
    :ivar _default_db: The default database client
    :vartype _default_db: Any
    '''

    class DBTypes():
        '''Helper class registering the different types of databases that are handled by
        :class:`cookbase.db.handler.DBHandler`.
        '''
        mongodb: str = 'mongodb'

    class InsertCBRResult(NamedTuple):
        '''A :mod:`namedtuple` containing the results from the :meth:`insert_cbr`
        method.

        '''
        cbr_id: Union[int, bool]
        cbrgraph_id: Optional[Union[int, bool]] = None

    InsertCBRResult.cbr_id.__doc__ = (
        'Field taking an integer representing the '
        'database identifier of the inserted :ref:`Cookbase Recipe (CBR) <cbr>`, or a '
        ':const:`False` boolean value in case of an unsuccessful '
        'insertion\n\n**type:** int or bool'
    )
    InsertCBRResult.cbrgraph_id.__doc__ = (
        'Field taking an integer representing the '
        'database identifier of the inserted :doc:`Cookbase Recipe Graph (CBRGraph) '
        '<cbrg>`, a :const:`False` boolean value in case of an unsuccessful insertion, '
        'or :const:`None` if :doc:`CBRGraph <cbrg>` insertion was not '
        'performed\n\n**type:** int or bool, optional'
    )

    def __init__(self, mongodb_url: str, db_type: str = DBTypes.mongodb,
                 db_name: str = 'cookbase'):
        '''Constructor method.'''
        if db_type == self.DBTypes.mongodb:
            self._default_db_id = db_type + ':' + db_name

            try:
                client = pymongo.MongoClient(mongodb_url + '/' + db_name)
                client.admin.command('ismaster')
            except pymongo.errors.PyMongoError:
                import sys
                raise DBClientConnectionError(
                    self._default_db_id).with_traceback(sys.exc_info()[2])

            self._default_db = client[db_name]
            self._connections = {self._default_db_id: self._default_db}
        else:
            raise InvalidDBTypeError(db_type)

    def get_db_client(self, db_id: str = 'mongodb:cookbase') -> Any:
        '''Retrieves the requested database client.

        :param db_id: A database identifier with the form :samp:`'{db_type}:{db_name}'`,
          defaults to :const:`None`
        :type db_id: str, optional
        :return: The requested database client
        :rtype: Any

        :raises cookbase.db.exceptions.InvalidDBTypeError: The database type is not
          valid
        :raises cookbase.db.exceptions.DBNotRegisteredError: The database client is not
          registered
        '''
        db_type = db_id.split(':')[0]
        if db_type == self.DBTypes.mongodb:
            if db_id in self._connections:
                return self._connections[db_id].client
            else:
                raise DBNotRegisteredError(db_id)
        else:
            raise InvalidDBTypeError(db_type)

    @demongofy
    def get_cbi(self, cbi_id: int) -> Dict[str, Any]:
        '''Retrieves a :ref:`Cookbase Ingredient (CBI) <cbi>` from database.

        :param int cbi_id: :ref:`CBI <cbi>` identifier
        :return: The requested :ref:`CBI <cbi>`
        :rtype: dict[str, Any]
        '''
        return self._default_db.cbi.find_one(cbi_id)

    @demongofy
    def get_cba(self, cba_id: int) -> Dict[str, Any]:
        '''Retrieves a :ref:`Cookbase Appliance (CBA) <cba>` from database.

        :param int cba_id: :ref:`CBA <cba>` identifier
        :return: The requested :ref:`CBA <cba>`
        :rtype: dict[str, Any]
        '''
        return self._default_db.cba.find_one(cba_id)

    @demongofy
    def get_cbp(self, cbp_id: int) -> Dict[str, Any]:
        '''Retrieves a :ref:`Cookbase Process (CBP) <cbp>` from database.

        :param int cbp_id: :ref:`CBP <cbp>` identifier
        :return: The requested :ref:`CBP <cbp>`
        :rtype: dict[str, Any]
        '''
        return self._default_db.cbp.find_one(cbp_id)

    @demongofy
    def get_cbr(self, query: Dict[str, Any]) -> Dict[str, Any]:
        '''Retrieves a :ref:`CBR <cbr>` from database.

        :param query: A dictionary specifying the query
        :type query: dict[str, Any]
        :return: The requested :ref:`CBR <cbr>`
        :rtype: dict[str, Any]
        '''
        return self._default_db.cbr.find_one(query)

    def insert_cbr(self, cbr: Dict[str, Any],
                   graph: Optional[Dict[str, Any]] = None) -> Optional[NamedTuple]:
        '''Inserts a :ref:`CBR <cbr>` into database with its :doc:`CBRGraph <cbrg>` (if
        given).

        :param cbr: A dictionary representing the :ref:`CBR <cbr>`
        :type cbr: dict[str, Any]
        :param graph: A dictionary representing the :doc:`CBRGraph <cbrg>`
        :type graph: dict[str, Any], optional
        :return: A :class:`InsertCBRResult` object holding the insertion results.
        :rtype: InsertCBRResult

        :raises cookbase.db.exceptions.BadCBRGraphError: The provided :doc:`CBRGraph
          <cbrg>` in `graph` is not valid
        :raises pymongo.errors.PyMongoError: Database error produced during insertion
        '''
        try:
            r_cbr = self._default_db.cbr.insert_one(cbr)
        except pymongo.errors.PyMongoError:
            raise

        if not r_cbr.acknowledged:
            return self.InsertCBRResult(False, None)
        elif not graph:
            return self.InsertCBRResult(r_cbr.inserted_id, None)
        else:
            graph['_id'] = ObjectId(str(r_cbr.inserted_id))

            try:
                graph['graph']['cbrId'] = str(graph['_id'])
            except KeyError:
                import sys
                raise BadCBRGraphError().with_traceback(sys.exc_info()[2])

            try:
                r_graph = self._default_db.cbrgraphs.insert_one(graph)
            except pymongo.errors.PyMongoError:
                raise

            if not r_graph.acknowledged:
                return self.InsertCBRResult(r_cbr.inserted_id, False)
            else:
                return self.InsertCBRResult(r_cbr.inserted_id, r_graph.inserted_id)


def get_handler(credentials_path=os.path.join(
        pathlib.Path(__file__).parent.absolute(), '../../credentials.txt')):
    '''Provides the database handler instance.

    The first time this function is called, a :class:`DBHandler` object is instantiated
    and returned according to the credentials provided in the file located at
    `credentials_path`; if called after the first time, it returns the already available
    instance, disregarding the given argument.

    :param credentials_path: A dictionary representing the :ref:`CBR <cbr>`
    :type credentials_path: str
    :return: A :class:`DBHandler` instance connected to the default database.
    :rtype: DBHandler
    '''
    if not cookbase.db.handler._db_handler:
        with open(credentials_path) as f:
            mongodb_url = f.readline()

        cookbase.db.handler._db_handler = DBHandler(mongodb_url, 'mongodb', 'cookbase')

    return cookbase.db.handler._db_handler


_db_handler = None


if __name__ == '__main__':
    test_db_handler = init()
    print(test_db_handler.get_cbr({'info.name': 'Pizza mozzarella'}))
