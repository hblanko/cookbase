from typing import Any, Dict

from pymongo import MongoClient


class MongoDBConnector(object):
    '''Class handling a connection to a MongoDB instance where recipes in Cookbase Recipe Format are stored.

    :ivar str db: Name of the MongoDB database where collections are stored
    :ivar url: The URL to the MongoDB server
    :vartype url: str, optional
    '''

    def __init__(self,
                 db: str,
                 url: str = None):
        '''Constructor method'''
        client = MongoClient(url)
        self.db = getattr(client, db)
        
    def find_one(self,
                 collection: str,
                 query: Dict[str, Any]) -> Dict[str, Any]:
        '''Returns a single document from the database

        :param str collection: Name of the database collection to query
        :param query: A dictionary specifying the query
        :type query: dict[str, Any]
        :return: the document obtained from query
        :rtype: dict[str, Any]
        '''
        return getattr(self.db, collection).find_one(query)
