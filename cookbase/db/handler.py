from typing import Any, Dict, Union

from bson.objectid import ObjectId
from pymongo import MongoClient

from cookbase.db.exceptions import DBNotRegisteredError, DBTypeError
from cookbase.db.utils import demongofy


class DBHandler():
    '''A class that handles connections to database instances.

    :param str mongodb_url: A `MongoDB connection URI
      <https://docs.mongodb.com/manual/reference/connection-string/>`_ to use as
      default database
    :param str db_type: An identifier of the database connection to use, defaults to
      :attr:`DBTypes.mongodb`
    :param str db_name: The name of the database to connect to, defaults to
      :const:`'cookbase'`

    :raises Exception: The database connection could not be established

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
        mongodb = 'mongodb'

    def __init__(self, mongodb_url: str, db_type: str = DBTypes.mongodb,
                 db_name: str = 'cookbase'):
        '''Constructor method.'''
        try:
            if db_type == 'mongodb':
                self._default_db_id = db_type + ':' + db_name
                self._connections = {
                    self._default_db_id: MongoClient(
                        mongodb_url + '/' + db_name
                    )[db_name]
                }
                self._default_db = self._connections[self._default_db_id]
        except Exception as e:
            raise e

    def get_db_client(self, db_id: str = None) -> Any:
        '''Retrieves the requested database client.

        :param db_id: A database identifier with the form :samp:`'{db_type}:{db_name}'`,
          defaults to :const:`None`
        :type db_id: str, optional
        :return: The requested database client
        :rtype: Any

        :raises cookbase.db.exceptions.DBTypeError: The database type is not implemented
        :raises cookbase.db.exceptions.DBNotRegisteredError: The database client is not
          registered
        '''
        if not db_id:
            db_id = self._default_db_id

        db_type = db_id.split(':')[0]
        if db_type == self.DBTypes.mongodb:
            if db_id in self._connections:
                return self._connections[db_id].client
            else:
                raise DBNotRegisteredError(db_id)
        else:
            raise DBTypeError(db_type)

    @demongofy
    def get_cbi(self, cbi_id: int) -> Dict[str, Any]:
        '''Retrieves a Cookbase Ingredient from database.

        :param int cbi_id: Cookbase Ingredient identifier
        :return: The requested Cookbase Ingredient
        :rtype: dict[str, Any]
        '''
        return self._default_db.cbi.find_one(cbi_id)

    @demongofy
    def get_cba(self, cba_id: int) -> Dict[str, Any]:
        '''Retrieves a Cookbase Appliance from database.

        :param int cba_id: Cookbase Appliance identifier
        :return: The requested Cookbase Appliance
        :rtype: dict[str, Any]
        '''
        return self._default_db.cba.find_one(cba_id)

    @demongofy
    def get_cbp(self, cbp_id: int) -> Dict[str, Any]:
        '''Retrieves a Cookbase Process from database.

        :param int cbp_id: Cookbase Process identifier
        :return: The requested Cookbase Process
        :rtype: dict[str, Any]
        '''
        return self._default_db.cbp.find_one(cbp_id)

    @demongofy
    def get_cbr(self, query: Dict[str, Any]) -> Dict[str, Any]:
        '''Retrieves a Cookbase Recipe from database.

        :param query: A dictionary specifying the query
        :type query: dict[str, Any]
        :return: The requested Cookbase Recipe
        :rtype: dict[str, Any]
        '''
        return self._default_db.cbr.find_one(query)

    def insert_cbr(self, cbr: Dict[str, Any],
                   graph: Dict[str, Any] = None) -> Union[int, bool]:
        '''Inserts a Cookbase Recipe into database with its CBRGraph (if given).

        :param cbr: A dictionary representing the Cookbase Recipe
        :type cbr: dict[str, Any]
        :param graph: A dictionary representing the CBRGraph
        :type graph: dict[str, Any], optional
        :return: The identifier of the stored object if CBR and CBRGraph insertion was
          successful, :const:`False` otherwise
        :rtype: int or bool
        '''
        r = self._default_db.cbr.insert_one(cbr)

        if not r.acknowledged:
            return False
        elif graph:
            graph['_id'] = ObjectId(str(r.inserted_id))
            graph['graph']['cbrId'] = str(graph['_id'])
            r = self._default_db.cbrgraphs.insert_one(graph)

            if not r.acknowledged:
                return False
        return r.inserted_id


# Default behavior
# mongodb_url = input('Enter MongoDB URI: ')
with open('../credentials.txt', 'r') as f:
    mongodb_url = f.readline()
db_handler = DBHandler(mongodb_url, 'mongodb', 'cookbase')
