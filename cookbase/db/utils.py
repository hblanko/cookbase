from functools import wraps
from typing import Callable


def underscore_id(o):
    try:
        o["_id"] = o["id"]
        del o["id"]
    finally:
        return o


def deunderscore_id(o):
    try:
        o["id"] = o["_id"]
        del o["_id"]
    finally:
        return o


def demongofy(f: Callable):
    """Decorator function that processes a JSON document retrieved from MongoDB.

    :param f: The decorated function
    :type f: Callable
    """

    @wraps(f)
    def wrapper(*args, **kwargs):
        return deunderscore_id(f(*args, **kwargs))

    return wrapper
