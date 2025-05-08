# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import UserError
import os
from datetime import datetime


@tagged('post_install', '-at_install')
class TestPredictRevenueHistory(TransactionCase):
    """Test suite for the Predict Revenue History model"""

    @classmethod
    def setUpClass(cls):
        super(TestPredictRevenueHistory, cls).setUpClass()

        # Create test product
        product_category = cls.env['product.category'].create({
            'name': 'Test Category',
        })

        cls.test_product = cls.env['product.product'].create({
            'name': 'Test Product History',
            'default_code': 'TEST002',
            'type': 'consu',
            'categ_id': product_category.id,
            'lst_price': 100.0,
            'standard_price': 50.0,
        })

        # Model to test
        cls.History = cls.env['predict.revenue.history']

    def test_01_create_history_record(self):
        """Test creating history records"""
        history = self.History.create({
            'product_id': self.test_product.id,
            'predict_year': '2025',
            'predict_month': '3',
            'predicted_quantity': 125.0,
            'prediction_date': datetime.now(),
        })

        self.assertTrue(history, "History record should be created")
        self.assertEqual(history.product_id.id, self.test_product.id)
        self.assertEqual(history.predict_year, '2025')
        self.assertEqual(history.predict_month, '3')
        self.assertEqual(history.predicted_quantity, 125.0)
        self.assertTrue(history.prediction_date)

    def test_02_search_and_order(self):
        """Test search and ordering functionality"""
        # Create multiple history records
        for month, qty in [('1', 100), ('2', 110), ('3', 120)]:
            self.History.create({
                'product_id': self.test_product.id,
                'predict_year': '2025',
                'predict_month': month,
                'predicted_quantity': qty,
                'prediction_date': datetime.now(),
            })

        # Test default ordering - newest first
        records = self.History.search([
            ('product_id', '=', self.test_product.id),
            ('predict_year', '=', '2025')
        ])

        # Should be in descending order by month
        self.assertEqual(records[0].predict_month, '3')
        self.assertEqual(records[1].predict_month, '2')
        self.assertEqual(records[2].predict_month, '1')

        # Test ordering by quantity
        records = self.History.search([
            ('product_id', '=', self.test_product.id),
            ('predict_year', '=', '2025')
        ], order='predicted_quantity asc')

        # Should be in ascending order by quantity
        self.assertEqual(records[0].predict_month, '1')
        self.assertEqual(records[1].predict_month, '2')
        self.assertEqual(records[2].predict_month, '3')

    def test_03_multi_year_data(self):
        """Test history records across multiple years"""
        # Create records for different years
        for year, month, qty in [('2025', '12', 150), ('2026', '1', 160)]:
            self.History.create({
                'product_id': self.test_product.id,
                'predict_year': year,
                'predict_month': month,
                'predicted_quantity': qty,
                'prediction_date': datetime.now(),
            })

        # Get records for 2025
        records_2025 = self.History.search([
            ('product_id', '=', self.test_product.id),
            ('predict_year', '=', '2025')
        ])

        # Test filtering by year
        self.assertTrue(all(r.predict_year == '2025' for r in records_2025))

        # Get records for 2026
        records_2026 = self.History.search([
            ('product_id', '=', self.test_product.id),
            ('predict_year', '=', '2026')
        ])

        self.assertTrue(all(r.predict_year == '2026' for r in records_2026))

        # Test ordering across years
        all_records = self.History.search([
            ('product_id', '=', self.test_product.id),
        ])

        # Default ordering should have 2026 first (newer), then 2025
        self.assertEqual(all_records[0].predict_year, '2026')

        # Test multiple products
        other_product = self.env['product.product'].create({
            'name': 'Other Test Product',
            'default_code': 'OTHER001',
        })

        self.History.create({
            'product_id': other_product.id,
            'predict_year': '2025',
            'predict_month': '6',
            'predicted_quantity': 200.0,
            'prediction_date': datetime.now(),
        })

        # Should not affect the records for the test product
        test_product_records = self.History.search([
            ('product_id', '=', self.test_product.id),
        ])

        # We only created 2 records in this test method
        self.assertEqual(len(test_product_records), 2)  # Only the 2 records from this test
        self.assertTrue(all(r.product_id.id == self.test_product.id for r in test_product_records))

        # Verify filtering works correctly
        other_product_records = self.History.search([
            ('product_id', '=', other_product.id),
        ])

        self.assertEqual(len(other_product_records), 1)
        self.assertEqual(other_product_records[0].product_id.id, other_product.id)

    def test_04_update_history_record(self):
        """Test updating history records"""
        # Create a record
        history = self.History.create({
            'product_id': self.test_product.id,
            'predict_year': '2026',
            'predict_month': '6',
            'predicted_quantity': 180.0,
            'prediction_date': datetime.now(),
        })

        # Update the record
        history.write({
            'predicted_quantity': 190.0,
            'prediction_date': datetime.now(),
        })

        # Verify update
        self.assertEqual(history.predicted_quantity, 190.0)

        # Find the record again
        record = self.History.search([
            ('product_id', '=', self.test_product.id),
            ('predict_year', '=', '2026'),
            ('predict_month', '=', '6')
        ], limit=1)

        self.assertEqual(record.id, history.id)
        self.assertEqual(record.predicted_quantity, 190.0)

    def test_05_selection_field_validation(self):
        """Test validation of selection fields"""
        # Valid values should create record
        history = self.History.create({
            'product_id': self.test_product.id,
            'predict_year': '2026',
            'predict_month': '12',
            'predicted_quantity': 200.0,
            'prediction_date': datetime.now(),
        })

        self.assertTrue(history)

        # Invalid year should raise error
        with self.assertRaises(ValueError):
            self.History.create({
                'product_id': self.test_product.id,
                'predict_year': '2024',  # Not in selection range
                'predict_month': '12',
                'predicted_quantity': 200.0,
            })

        # Invalid month should raise error
        with self.assertRaises(ValueError):
            self.History.create({
                'product_id': self.test_product.id,
                'predict_year': '2026',
                'predict_month': '13',  # Not in selection range
                'predicted_quantity': 200.0,
            })

    def test_06_required_fields(self):
        """Test validation of required fields"""
        History = self.env['predict.revenue.history']

        # Create a test product to use
        test_product = self.env['product.product'].create({
            'name': 'Required Fields Test Product',
            'default_code': 'REQ001',
        })

        # Test: All required fields present should work
        history = History.create({
            'product_id': test_product.id,
            'predict_year': '2026',
            'predict_month': '12',
            'predicted_quantity': 200.0,
        })
        self.assertTrue(history, "Record should be created when all required fields are present")

        # Verify the required fields are set correctly
        self.assertEqual(history.product_id.id, test_product.id)
        self.assertEqual(history.predict_year, '2026')
        self.assertEqual(history.predict_month, '12')
        self.assertEqual(history.predicted_quantity, 200.0)