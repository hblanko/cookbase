import os
import pathlib
from typing import Any, Dict, Optional, Union

import pymongo
import uritools
from attr import attrib, attrs
from bson.objectid import ObjectId
from cookbase.db.exceptions import (
    CBRGraphInsertionError,
    CBRInsertionError,
    DBClientConnectionError,
    DBNotRegisteredError,
    InvalidDBTypeError,
)
from cookbase.db.utils import demongofy
from cookbase.graph.cbrgraph import CBRGraph


@attrs
class InsertCBRResult:
    """A class containing the results from the :meth:`DBHandler.insert_cbr` method.

    :param cbr_id: Field taking the database identifier of the inserted :ref:`Cookbase
      Recipe (CBR) <cbr>`, or :const:`None` if the insertion was not performed, defaults
      to :const:`None`
    :type cbr_id: ObjectId, optional
    :param cbrgraph_id: Field taking the database identifier of the inserted
      :doc:`Cookbase Recipe Graph (CBRGraph) <cbrg>`, or :const:`None` if the insertion
      was not performed, defaults to :const:`None`
    :type cbrgraph_id: ObjectId, optional

    """

    cbr_id: Optional[ObjectId] = attrib(default=None)
    cbrgraph_id: Optional[ObjectId] = attrib(default=None)


class DBHandler:
    """A class that handles connections to database instances in order to store and
    retrieve the different :doc:`Cookbase Data Model (CBDM) <cbdm>` elements.

    :param str mongodb_url: A `MongoDB connection URI
      <https://docs.mongodb.com/manual/reference/connection-string/>`_ to use as
      default database
    :param str db_type: An identifier of the database connection to use, defaults to
      :attr:`DBTypes.MONGODB`
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
    """

    class DBTypes:
        """Helper class registering the different types of databases that are handled by
        :class:`cookbase.db.handler.DBHandler`.
        """

        MONGODB: str = "mongodb"

    def __init__(
        self,
        mongodb_url: str,
        db_type: str = DBTypes.MONGODB,
        db_name: str = "cookbase",
    ):
        """Constructor method."""
        if db_type == self.DBTypes.MONGODB:
            self._default_db_id: str = f"{db_type}:{db_name}"

            try:
                client = pymongo.MongoClient(uritools.urijoin(mongodb_url, db_name))
                client.admin.command("ismaster")
            except pymongo.errors.PyMongoError:
                import sys

                raise DBClientConnectionError(self._default_db_id).with_traceback(
                    sys.exc_info()[2]
                )

            self._default_db: Any = client[db_name]
            self._connections: Dict[str, Any] = {self._default_db_id: self._default_db}
        else:
            raise InvalidDBTypeError(db_type)

    def get_db_client(self, db_id: str = "mongodb:cookbase") -> Any:
        """Retrieves the requested database client.

        :param db_id: A database identifier with the form :samp:`'{db_type}:{db_name}'`,
          defaults to :const:`None`
        :type db_id: str, optional
        :return: The requested database client
        :rtype: Any

        :raises cookbase.db.exceptions.InvalidDBTypeError: The database type is not
          valid
        :raises cookbase.db.exceptions.DBNotRegisteredError: The database client is not
          registered
        """
        db_type = db_id.split(":")[0]
        if db_type == self.DBTypes.MONGODB:
            if db_id in self._connections:
                return self._connections[db_id].client
            else:
                raise DBNotRegisteredError(db_id)
        else:
            raise InvalidDBTypeError(db_type)

    @demongofy
    def get_cbi(self, cbi_id: int) -> Dict[str, Any]:
        """Retrieves a :ref:`Cookbase Ingredient (CBI) <cbi>` from database.

        :param int cbi_id: :ref:`CBI <cbi>` identifier
        :return: The requested :ref:`CBI <cbi>`
        :rtype: dict[str, Any]
        """
        return self._default_db.cbi.find_one(cbi_id)

    @demongofy
    def get_cba(self, cba_id: int) -> Dict[str, Any]:
        """Retrieves a :ref:`Cookbase Appliance (CBA) <cba>` from database.

        :param int cba_id: :ref:`CBA <cba>` identifier
        :return: The requested :ref:`CBA <cba>`
        :rtype: dict[str, Any]
        """
        return self._default_db.cba.find_one(cba_id)

    @demongofy
    def get_cbp(self, cbp_id: int) -> Dict[str, Any]:
        """Retrieves a :ref:`Cookbase Process (CBP) <cbp>` from database.

        :param int cbp_id: :ref:`CBP <cbp>` identifier
        :return: The requested :ref:`CBP <cbp>`
        :rtype: dict[str, Any]
        """
        return self._default_db.cbp.find_one(cbp_id)

    @demongofy
    def get_cbr(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Retrieves a :ref:`CBR <cbr>` from database.

        :param query: A dictionary specifying the query
        :type query: dict[str, Any]
        :return: The requested :ref:`CBR <cbr>`
        :rtype: dict[str, Any]
        """
        return self._default_db.cbr.find_one(query)

    def insert_cbr(
        self, cbr: Dict[str, Any], cbrgraph: Optional[CBRGraph] = None
    ) -> InsertCBRResult:
        """Inserts a :ref:`CBR <cbr>` into database with its :doc:`CBRGraph <cbrg>` (if
        given).

        :param cbr: A dictionary representing the :ref:`CBR <cbr>`
        :type cbr: dict[str, Any]
        :param cbrgraph: A dictionary representing the :doc:`CBRGraph <cbrg>`
        :type cbrgraph: dict[str, Any], optional
        :return: A :class:`InsertCBRResult` object holding the insertion results.
        :rtype: InsertCBRResult

        :raises CBRInsertionError: The :ref:`CBR <cbr>` could not be stored
        :raises CBRGraphInsertionError: The :doc:`CBRGraph <cbrg>` could not be stored
        :raises pymongo.errors.PyMongoError: Database error produced during insertion
        """
        try:
            r_cbr = self._default_db.cbr.insert_one(cbr)
        except pymongo.errors.PyMongoError:
            raise

        if not r_cbr.acknowledged:
            raise CBRInsertionError(InsertCBRResult())
        elif not cbrgraph:
            return InsertCBRResult(cbr_id=r_cbr.inserted_id)
        else:
            cbrgraph_dict = cbrgraph.get_serializable_graph()
            cbrgraph_dict["_id"] = ObjectId(str(r_cbr.inserted_id))
            cbrgraph_dict["graph"]["cbrId"] = str(cbrgraph_dict["_id"])

            try:
                r_graph = self._default_db.cbrgraphs.insert_one(cbrgraph_dict)
            except pymongo.errors.PyMongoError:
                raise

            if not r_graph.acknowledged:
                raise CBRGraphInsertionError(InsertCBRResult(cbr_id=r_cbr.inserted_id))
            else:
                return InsertCBRResult(
                    cbr_id=r_cbr.inserted_id, cbrgraph_id=r_graph.inserted_id
                )

    def close_connections(self):
        """Closes all connections registered by this :class:`DBHandler` object."""
        try:
            for k, v in self._connections.items():
                if k.split(":")[0] == self.DBTypes.MONGODB:
                    v.client.close()

            self._connections.clear()
        except AttributeError:
            pass

    def __del__(self):
        """Destructor method."""
        self.close_connections()


def get_handler(
    credentials_path: Optional[str] = None, force_new_instance: bool = False
):
    """Provides the database handler instance.

    The first time this function is called (or if the `force_new_instance` flag is set
    to :const:`True`) a :class:`DBHandler` object is instantiated and returned according
    to the credentials provided in the file located at `credentials_path`; if called
    after the first time (and being the `force_new_instance` flag set to
    :const:`False`), it returns the already available instance, disregarding the
    `credentials_path` argument.

    :param credentials_path: Path to the file containing the connection credentials
    :type credentials_path: str or None, optional
    :param force_new_instance: A flag indicating whether a new database handler
      instance must be initialized, defaults to :const:`False`
    :type force_new_instance: bool, optional
    :return: A :class:`DBHandler` instance connected to the default database
    :rtype: DBHandler
    """
    global _db_handler

    if not _db_handler or force_new_instance:
        if not credentials_path:
            credentials_path = os.path.join(
                pathlib.Path(__file__).parent.absolute(), "../../credentials.txt"
            )

        with open(credentials_path) as f:
            mongodb_url = f.readline()

        _db_handler = DBHandler(mongodb_url, "mongodb", "cookbase")

    return _db_handler


_db_handler = None


if __name__ == "__main__":
    from pprint import pprint

    pprint(get_handler().get_cbr({"info.name": "Pizza mozzarella"}))
