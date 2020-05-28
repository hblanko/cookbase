import unittest
from unittest import mock

import jsonschema
from bson.objectid import ObjectId
from cookbase.db import exceptions, handler
from cookbase.parsers.utils import parse_cbr
from cookbase.validation import cbr


class TestCbrValidation(unittest.TestCase):
    """Test class for the :mod:`cookbase.validation.cbr` module.

    """

    test_exhaustive = False

    def setUp(self):
        self.good_cbr = parse_cbr("resources/pizza-mozzarella.cbr")
        self.bad_cbr = parse_cbr("resources/pizza-demigrella.cbr")
        self.validator = cbr.Validator()

    @mock.patch.object(handler.DBHandler, "insert_cbr", autospec=True)
    def test__store(self, mock_insert_cbr):
        """Tests the :class:`cookbase.validation.cbr.Validator._store` method."""
        # -- Testing correct result ----------------------------------------------------
        self.validator._store(self.good_cbr)
        mock_insert_cbr.assert_called_once()

    @unittest.skipIf(
        not test_exhaustive, "test_apply_validation_rules() explicitly skipped"
    )
    def test_apply_validation_rules(self):
        """Tests the :meth:`cookbase.validation.cbr.Validator.apply_validation_rules`
        method.
        """
        # -- Testing correct results ---------------------------------------------------
        results = self.validator.apply_validation_rules(self.good_cbr)
        self.assertEqual(results.is_valid(strict=False), True)

        results = self.validator.apply_validation_rules(self.bad_cbr)
        self.assertEqual(results.is_valid(strict=False), False)

    @mock.patch.object(cbr.Validator, "_store", autospec=True)
    @mock.patch.object(cbr.Validator, "apply_validation_rules", autospec=True)
    @mock.patch.object(jsonschema, "validate", autospec=True)
    def test_validate(
        self, mock_jsonschema_validate, mock_apply_validation_rules, mock__store
    ):
        """Tests the :class:`cookbase.validation.cbr.Validator.validate` method."""
        # -- Testing correct results ---------------------------------------------------
        mock_apply_validation_rules.return_value = cbr.ValidationResult()
        id = ObjectId()
        mock__store.return_value = handler.InsertCBRResult(cbr_id=id, cbrgraph_id=id)

        result = self.validator.validate(self.good_cbr, strict=False)
        self.assertEqual(result.storing_result, None)

        result = self.validator.validate(self.good_cbr, store=True, strict=False)
        self.assertEqual(result.storing_result, mock__store.return_value)

        # -- Testing CBRInsertionError -------------------------------------------------
        mock__store.side_effect = exceptions.CBRInsertionError(
            handler.InsertCBRResult()
        )

        result = self.validator.validate(self.good_cbr, store=True, strict=False)
        self.assertEqual(result.storing_result, mock__store.side_effect.partial_result)

        # -- Testing CBRGraphInsertionError --------------------------------------------
        mock__store.side_effect = exceptions.CBRGraphInsertionError(
            handler.InsertCBRResult(cbr_id=ObjectId())
        )

        result = self.validator.validate(self.good_cbr, store=True, strict=False)
        self.assertEqual(result.storing_result, mock__store.side_effect.partial_result)


if __name__ == "__main__":
    unittest.main()
