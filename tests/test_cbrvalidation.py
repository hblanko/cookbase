import json
import unittest

from cookbase.validation.cbr import CbrValidation
from cookbase.validation.exceptions import CbrValidationError


class TestCbrValidation(unittest.TestCase):
    '''Test class for the `cookbase.validation` package.'''

    def test_validate_instruments_usage(self):
        '''Testing the `Validation.validate_instruments_usage` method'''
        with open("./resources/proc1.json") as json_file:
            data = json.load(json_file)
            json_file.close()

        v = CbrValidation("http://www.landarltracker.com/schemas")
        v._instruments = dict()
        for i in data["instruments"].keys():
            v._instruments[i] = [data["instruments"][i], "PROC1000"]

        with self.assertRaises(CbrValidationError):
            v._validate_instruments_usage("proc1", data["preparation"]["proc1"], (*data["preparation"]["proc1"]["foodstuffsList"],), ((("family", "container"),),))

    def test_validate_recipe(self):
        '''Testing the `Validation.validate_recipe` method'''
        with open("./resources/pizzaMozzarella.json") as json_file:
            data = json.load(json_file)
            json_file.close()
        v = CbrValidation("http://www.landarltracker.com/schemas")
        v.validate_recipe(data)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
