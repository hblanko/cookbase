import unittest

from cookbase.parsers import utils
from cookbase.validation.cbr import Validator


class TestCbrValidator(unittest.TestCase):
    '''Test class for the `cookbase.validation` package.'''

#     def test__store(self):
#         '''Testing the `Validator._store` method'''
#         # TODO
#         pass

    def test_validate_recipe(self):
        '''Testing the `Validation.validate_recipe` method'''
        recipe_path = "../resources/cbr/pizzaMozzarella.json"
        recipe = utils.parse_json_recipe(recipe_path)
        result = Validator().validate(recipe, store=False)
        for i in result.values():
            self.assertTrue(i)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
