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


def demongofy(function):
    def deunderscore_id(cls, a):
        o = function(cls, a)
        try:
            o["id"] = o["_id"]
            del o["_id"]
        finally:
            return o
    return deunderscore_id
