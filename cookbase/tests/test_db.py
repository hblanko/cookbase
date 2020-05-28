import os
import pathlib
import unittest

import pymongo
from cookbase.db import exceptions, handler, utils
from cookbase.graph.cbrgraph import CBRGraph


class TestDBHandler(unittest.TestCase):
    """Test class for the :mod:`cookbase.db.handler` module.

    """

    test_exhaustive = True

    def setUp(self):
        self.db_handler = handler.get_handler()

    @unittest.skipIf(not test_exhaustive, "test___init__() explicitly skipped")
    def test___init__(self):
        """Tests the :class:`cookbase.db.handler.DBHandler` constructor method."""
        # ===============================================================================
        # # -- Testing cookbase.db.exceptions.DBClientConnectionError --
        # # INFO: Disallowed as it triggers a time-out wait
        # ===============================================================================
        # with self.assertRaises(exceptions.DBClientConnectionError):
        #    handler.DBHandler('randommongodburl123456789')
        # ===============================================================================

        credentials_path = os.path.join(
            pathlib.Path(__file__).parent.absolute(), "../../credentials.txt"
        )

        with open(credentials_path) as f:
            mongodb_url = f.readline()

        # -- Testing cookbase.db.exceptions.DBClientConnectionError (invalid database
        # -- name) -----------------------------------------------------
        with self.assertRaises(exceptions.DBClientConnectionError):
            handler.DBHandler(
                mongodb_url,
                db_type=handler.DBHandler.DBTypes.MONGODB,
                db_name="invalid$db$name",
            )

        # -- Testing cookbase.db.exceptions.InvalidDBTypeError (invalid database type) -
        with self.assertRaises(exceptions.InvalidDBTypeError):
            handler.DBHandler(mongodb_url, db_type="FakeQL", db_name="valid_name")

    def test_get_db_client(self):
        """Tests the :meth:`cookbase.db.handler.DBHandler.get_db_client` method."""
        # -- Testing correct result ----------------------------------------------------
        self.assertIsNotNone(self.db_handler.get_db_client())

        # -- Testing cookbase.db.exceptions.InvalidDBTypeError -------------------------
        with self.assertRaises(exceptions.InvalidDBTypeError):
            self.db_handler.get_db_client("FakeQL:cookbase")

        # -- Testing cookbase.db.exceptions.DBNotRegisteredError -----------------------
        with self.assertRaises(exceptions.DBNotRegisteredError):
            self.db_handler.get_db_client("mongodb:foobase")

    def test_get_cbi(self):
        """Tests the :meth:`cookbase.db.handler.DBHandler.get_cbi` method."""
        test_dict = {"unit": "test"}
        result = self.db_handler._default_db.cbi.insert_one(test_dict)
        self.assertEqual(
            self.db_handler.get_cbi(result.inserted_id),
            utils.deunderscore_id(test_dict),
        )
        self.db_handler._default_db.cbi.delete_one({"_id": result.inserted_id})

    def test_get_cba(self):
        """Tests the :meth:`cookbase.db.handler.DBHandler.get_cba` method."""
        test_dict = {"unit": "test"}
        result = self.db_handler._default_db.cba.insert_one(test_dict)
        self.assertEqual(
            self.db_handler.get_cba(result.inserted_id),
            utils.deunderscore_id(test_dict),
        )
        self.db_handler._default_db.cba.delete_one({"_id": result.inserted_id})

    def test_get_cbp(self):
        """Tests the :meth:`cookbase.db.handler.DBHandler.get_cbp` method."""
        test_dict = {"unit": "test"}
        result = self.db_handler._default_db.cbp.insert_one(test_dict)
        self.assertEqual(
            self.db_handler.get_cbp(result.inserted_id),
            utils.deunderscore_id(test_dict),
        )
        self.db_handler._default_db.cbp.delete_one({"_id": result.inserted_id})

    def test_get_cbr(self):
        """Tests the :meth:`cookbase.db.handler.DBHandler.get_cbr` method."""
        test_dict = {"unit": "test"}
        result = self.db_handler._default_db.cbr.insert_one(test_dict)
        self.assertEqual(
            self.db_handler.get_cbr(result.inserted_id),
            utils.deunderscore_id(test_dict),
        )
        self.db_handler._default_db.cbr.delete_one({"_id": result.inserted_id})

    def test_insert_cbr(self):
        """Tests the :meth:`cookbase.db.handler.DBHandler.insert_cbr` method."""
        test_dict = {"unit": "test"}
        test_graph = CBRGraph()

        # -- Testing correct result ------------------------------------
        results = self.db_handler.insert_cbr(test_dict, test_graph)
        expected_results = handler.InsertCBRResult(test_dict["_id"], test_dict["_id"])
        self.assertEqual(results, expected_results)

        if results.cbr_id:
            self.db_handler._default_db.cbr.delete_one({"_id": results.cbr_id})

        if results.cbrgraph_id:
            self.db_handler._default_db.cbrgraphs.delete_one(
                {"_id": results.cbrgraph_id}
            )

        # -- Testing correct result (without CBRGraph insertion) -------
        results = self.db_handler.insert_cbr(test_dict)
        expected_results = handler.InsertCBRResult(test_dict["_id"])
        self.assertEqual(results, expected_results)

        # -- Testing pymongo.errors.PyMongoError (DuplicateKeyError) ---
        from bson.objectid import ObjectId

        with self.assertRaises(pymongo.errors.PyMongoError) as cm:
            self.db_handler.insert_cbr({"_id": ObjectId(str(results.cbr_id))})

        if not isinstance(cm.exception, pymongo.errors.PyMongoError):
            self.db_handler._default_db.cbr.delete_one(
                {"_id": ObjectId(str(results.cbr_id))}
            )

        if results.cbr_id:
            self.db_handler._default_db.cbr.delete_one({"_id": results.cbr_id})

        # It has no effect in case of correct behavior, but done just in case
        if results.cbrgraph_id:
            self.db_handler._default_db.cbrgraphs.delete_one(
                {"_id": results.cbrgraph_id}
            )

        # It has no effect in case of correct behavior, but done just in case
        if results.cbrgraph_id:
            self.db_handler._default_db.cbrgraphs.delete_one(
                {"_id": results.cbrgraph_id}
            )

        # TODO: Cases where the insertions are not acknowledged are not tested

    @unittest.skipIf(not test_exhaustive, "test_close_connections() explicitly skipped")
    def test_close_connections(self):
        """Tests the :meth:`cookbase.db.handler.DBHandler.close_connections` method."""
        self.db_handler.close_connections()
        self.assertEqual(self.db_handler._connections, {})

        # Re-instantiate the database handler
        self.db_handler = handler.get_handler(force_new_instance=True)


if __name__ == "__main__":
    unittest.main()
