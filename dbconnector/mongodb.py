from typing import Any, Dict

from pymongo import MongoClient


class MongoDBConnector(object):
    '''Class performing validation and graph construction of recipes in JSON Cookbase Format.

    :ivar str db: The base path of the JSON Schema directory
    :ivar url: A structure storing data of remaining foodstuffs in preparation flow, defaults to `None`
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
