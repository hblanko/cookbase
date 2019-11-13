from typing import Any, Dict, Union

from bson.objectid import ObjectId
from pymongo import MongoClient

from cookbase.db.utils import demongofy
from cookbase.db.exceptions import DBTypeError, DBNotRegisteredError


class DBHandler(object):
    """Class handling connections to database instances

    :ivar str _default_db_id: The default database identifier with the form "<db_type>:<db_name>", defaults to "mongodb:cookbase"
    :ivar _connections: A dictionary containing the data about all the handled connections
    :vartype _connections: dict[str, Any]
    :ivar _default_db: The default database client
    :vartype _default_db: Any
    """

    class DBTypes():
        """Helper class registering the different types of databases that are handled by
        :class:`cookbase.db.handler.DBHandler`.
        """
        mongodb = "mongodb"

    def __init__(self, mongodb_url: str, db_type: str = DBTypes.mongodb,
                 db_name: str = "cookbase"):
        """Constructor method

        :param str mongodb_url: A MongoDB connection URI to use as default database
        :param str db_type: An identifier of the database connection to use, defaults to :attr:`DBTypes.mongodb`
        :param str db_name: The name of the database to connect to, defaults to "cookbase"
        """
        try:
            if db_type == "mongodb":
                self._default_db_id = db_type + ":" + db_name
                self._connections = {self._default_db_id: MongoClient(
                    mongodb_url + "/" +
                    db_name)[db_name]}
                self._default_db = self._connections[self._default_db_id]
        except Exception as e:
            raise e

    def get_db_client(self, db_id=None) -> Any:
        """Retrieves the requested database client

        :param str db_id: A database identifier with the form "<db_type>:<db_name>", defaults to None
        :return: the requested database client
        :rtype: Any
        :raises cookbase.db.exceptions.DBTypeError: The database type is not implemented
        :raises cookbase.db.exceptions.DBNotRegisteredError: The database client is not registered
        """
        if not db_id:
            db_id = self._default_db_id

        db_type = db_id.split(":")[0]
        if db_type == self.DBTypes.mongodb:
            if db_id in self._connections:
                return self._connections[db_id].client
            else:
                raise DBNotRegisteredError(db_id)
        else:
            raise DBTypeError(db_type)

    @demongofy
    def get_cbi(self,
                cbi_id: int) -> Dict[str, Any]:
        """Retrieves a Cookbase Ingredient from database

        :param int cbi_id: Cookbase Ingredient identifier
        :return: the requested Cookbase Ingredient
        :rtype: dict[str, Any]
        """
        return self._default_db.cbi.find_one(cbi_id)

    @demongofy
    def get_cba(self,
                cba_id: int) -> Dict[str, Any]:
        """Retrieves a Cookbase Appliance from database

        :param int cba_id: Cookbase Appliance identifier
        :return: the requested Cookbase Appliance
        :rtype: dict[str, Any]
        """
        return self._default_db.cba.find_one(cba_id)

    @demongofy
    def get_cbp(self,
                cbp_id: int) -> Dict[str, Any]:
        """Retrieves a Cookbase Process from database

        :param int cbp_id: Cookbase Process identifier
        :return: the requested Cookbase Process
        :rtype: dict[str, Any]
        """
        return self._default_db.cbp.find_one(cbp_id)

    @demongofy
    def get_cbr(self,
                query: Dict[str, Any]) -> Dict[str, Any]:
        """Retrieves a Cookbase Recipe from database

        :param query: A dictionary specifying the query
        :type query: dict[str, Any]
        :return: the requested Cookbase Recipe
        :rtype: dict[str, Any]
        """
        return self._default_db.cbr.find_one(query)

    def insert_cbr(self,
                   cbr: Dict[str, Any],
                   graph: Dict[str, Any] = None) -> Union[int, bool]:
        """Inserts a Cookbase Recipe into database, with its CBR-Graph (if given)

        :param cbr: A dictionary specifying the Cookbase Recipe
        :type cbr: dict[str, Any]
        :param graph: A dictionary specifying the recipe graph
        :type graph: dict[str, Any], optional
        :return: If CBR and CBR-Graph insertion was successful returns the id of the stored object,
        otherwise returns `False`
        :rtype: int or bool
        """
        r = self._default_db.cbr.insert_one(cbr)

        if not r.acknowledged:
            return False
        elif graph:
            graph["_id"] = ObjectId(str(r.inserted_id))
            graph["graph"]["cbrId"] = str(graph["_id"])
            r = self._default_db.cbrgraphs.insert_one(graph)
            if not r.acknowledged:
                return False
        return r.inserted_id


# Default behavior
mongodb_url = input("Enter MongoDB URI: ")
db_handler = DBHandler(mongodb_url, "mongodb", "cookbase")
