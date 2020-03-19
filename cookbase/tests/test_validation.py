import unittest
from unittest import mock

import jsonschema
from cookbase.db.handler import DBHandler
from cookbase.parsers.utils import parse_json_recipe
from cookbase.validation import cbr


class TestCbrValidation(unittest.TestCase):
    '''Test class for the :mod:`cookbase.validation.cbr` module.

    '''
    test_exhaustive = True

    def setUp(self):
        self.good_cbr = parse_json_recipe('resources/pizza-mozzarella.cbr')
        self.bad_cbr = parse_json_recipe('resources/pizza-demigrella.cbr')
        self.validator = cbr.Validator()

    @mock.patch.object(DBHandler, 'insert_cbr', autospec=True)
    def test__store(self, mock_insert_cbr):
        '''Tests the :class:`cookbase.validation.cbr.Validator._store` method.'''
        # -- Testing correct result ----------------------------------------------------
        self.validator._store(self.good_cbr)
        mock_insert_cbr.assert_called_once()

    @unittest.skipIf(not test_exhaustive,
                     'test_apply_validation_rules() explicitly skipped')
    def test_apply_validation_rules(self):
        '''Tests the :meth:`cookbase.validation.cbr.Validator.apply_validation_rules`
        method.
        '''
        # -- Testing correct results ---------------------------------------------------
        results = self.validator.apply_validation_rules(self.good_cbr)
        self.assertEqual(False in results.values(), False)

        results = self.validator.apply_validation_rules(self.bad_cbr)
        self.assertEqual(False in results.values(), True)

    @mock.patch.object(cbr.Validator, '_store', autospec=True)
    @mock.patch.object(cbr.Validator, 'apply_validation_rules', autospec=True)
    @mock.patch.object(jsonschema, 'validate', autospec=True)
    def test_validate(self, mock_jsonschema_validate,  mock_apply_validation_rules,
                      mock__store):
        '''Tests the :class:`cookbase.validation.cbr.Validator.validate` method.'''
        # -- Testing correct results ---------------------------------------------------
        mock_apply_validation_rules.return_value = {'testing': True}
        mock__store.return_value = 123456789

        result = self.validator.validate(self.good_cbr)
        self.assertNotIn('inserted_id', result.keys())

        result = self.validator.validate(self.good_cbr, store=True)
        self.assertEqual(result['inserted_id'], mock__store.return_value)


if __name__ == '__main__':
    unittest.main()
