# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import UserError
import os
import pandas as pd
import numpy as np
import unittest.mock as mock
import tempfile
import joblib
import json
from datetime import datetime


# Define mock classes at module level so they can be properly pickled
class MockPreprocessor:
    def transform(self, X):
        # Return a mock transformed array
        return np.array([[1.0, 2.0, 3.0, 4.0, 5.0]])

    def get_feature_names_out(self, cols):
        return [f"{col}_transformed" for col in cols]


class MockModel:
    def predict(self, X):
        # Always predict 150 for testing
        return np.array([150.0])


class MockPipeline:
    def __init__(self):
        self.named_steps = {
            'pre': MockPreprocessor(),
            'lgbm': MockModel()
        }


@tagged('post_install', '-at_install')
class TestPredictRevenueDashboard(TransactionCase):
    """Test suite for the Predict Revenue Dashboard module"""

    def setUp(self):
        super(TestPredictRevenueDashboard, self).setUp()

        # Create test product
        product_category = self.env['product.category'].create({
            'name': 'Test Category',
        })

        self.test_product = self.env['product.product'].create({
            'name': 'Test Product',
            'default_code': 'TEST001',
            'type': 'consu',
            'categ_id': product_category.id,
            'lst_price': 100.0,
            'standard_price': 50.0,
        })

        # Create a mock model and preprocessor
        self.create_mock_model_file()

        # Create history records
        self.create_history_records()

        # Create dashboard record
        self.dashboard = self.env['predict.revenue.dashboard'].create({
            'product_id': self.test_product.id,
            'predict_year': '2025',
            'predict_month': '6',
        })

    def create_mock_model_file(self):
        """Create a mock ML model file for testing"""
        # Create a mock pipeline using the classes defined at module level
        pipeline = MockPipeline()

        # Use a temporary directory instead of trying to write to the module directory
        temp_dir = tempfile.mkdtemp()
        self.model_path = os.path.join(temp_dir, 'model_lightgbm_optimized.pkl')

        # Save mock model to the temporary directory
        joblib.dump(pipeline, self.model_path)

        # Patch the model path in the actual code to use our temporary file
        self.patch_model_path()

    def patch_model_path(self):
        """Patch the model path in the actual code to use our temporary file"""
        # Instead of trying to patch methods, let's use mock.patch directly
        patcher = mock.patch('joblib.load', return_value=MockPipeline())
        self.addCleanup(patcher.stop)
        patcher.start()

    def create_history_records(self):
        """Create test history records"""
        History = self.env['predict.revenue.history']
        # Create 6 months of history data for the test product
        for month in range(1, 7):
            History.create({
                'product_id': self.test_product.id,
                'predict_year': '2025',
                'predict_month': str(month),
                'predicted_quantity': 100 + (month * 10),  # Incrementing values
                'prediction_date': datetime.now(),
            })

    def test_01_model_creation(self):
        """Test model creation and fields"""
        # Test Dashboard model
        dashboard = self.env['predict.revenue.dashboard'].create({
            'product_id': self.test_product.id,
            'predict_year': '2025',
            'predict_month': '7',
        })

        self.assertTrue(dashboard, "Dashboard record should be created")
        self.assertEqual(dashboard.product_id.id, self.test_product.id)
        self.assertEqual(dashboard.predicted_revenue, 0.0)  # Initial value

        # Test History model
        history = self.env['predict.revenue.history'].create({
            'product_id': self.test_product.id,
            'predict_year': '2025',
            'predict_month': '8',
            'predicted_quantity': 180.0,
            'prediction_date': datetime.now(),
        })

        self.assertTrue(history, "History record should be created")
        self.assertEqual(history.product_id.id, self.test_product.id)
        self.assertEqual(history.predicted_quantity, 180.0)

    def test_02_compute_chart_data(self):
        """Test chart data computation"""
        self.dashboard._compute_chart_data()

        # Verify chart data is properly formatted
        chart_data = json.loads(self.dashboard.chart_data)

        self.assertIn('labels', chart_data)
        self.assertIn('datasets', chart_data)
        self.assertEqual(len(chart_data['datasets']), 1)
        self.assertEqual(len(chart_data['labels']), 6)  # Should have 6 history items

        # Verify chart dummy computation
        self.dashboard._compute_chart_dummy()
        self.assertEqual(self.dashboard.chart_dummy, 'display')

        # Test chart data with a different product that has no history
        new_product = self.env['product.product'].create({
            'name': 'Empty History Product',
            'default_code': 'EMPTY001',
            'type': 'consu',
            'lst_price': 100.0,
            'standard_price': 50.0,
        })

        empty_dashboard = self.env['predict.revenue.dashboard'].create({
            'product_id': new_product.id,  # Use a valid product
            'predict_year': '2025',
            'predict_month': '7',
        })

        empty_dashboard._compute_chart_data()
        empty_chart_data = json.loads(empty_dashboard.chart_data)
        self.assertEqual(len(empty_chart_data['datasets'][0]['data']), 0)

    def test_03_sql_injection_protection(self):
        """Test protection against SQL injection in product data"""
        # Create a product with potentially dangerous SQL in its data
        sql_injection_product = self.env['product.product'].create({
            'name': "SQL Injection Test'; DROP TABLE ir_model; --",
            'default_code': "TEST'; DELETE FROM product_product; --",
            'type': 'consu',
            'lst_price': 100.0,
            'standard_price': 50.0,
        })

        # Create dashboard with the SQL injection product
        dashboard_sql = self.env['predict.revenue.dashboard'].create({
            'product_id': sql_injection_product.id,
            'predict_year': '2025',
            'predict_month': '6',
        })

        # This should run without SQL errors if parameters are properly sanitized
        dashboard_sql._onchange_predict_revenue()

        # Verify prediction still works
        self.assertEqual(dashboard_sql.predicted_revenue, 150.0)

        # Verify debug info contains the SQL injection string in the input data
        # The debug info contains the input data dictionary with the default_code
        self.assertIn("TEST'; DELETE FROM product_product; --", dashboard_sql.debug_info)

        # Verify history record was created properly
        history = self.env['predict.revenue.history'].search([
            ('product_id', '=', sql_injection_product.id),
            ('predict_year', '=', '2025'),
            ('predict_month', '=', '6')
        ])
        self.assertTrue(history)
        self.assertEqual(history.predicted_quantity, 150.0)

        # Verify that no tables were affected by the SQL injection attempt
        # This would raise an error if the ir_model table was dropped
        self.env['ir.model'].search([], limit=1)

    def test_04_onchange_predict_revenue_success(self):
        """Test the prediction workflow with successful prediction"""
        # Trigger onchange
        self.dashboard._onchange_predict_revenue()

        # Verify predicted value
        self.assertEqual(self.dashboard.predicted_revenue, 150.0)

        # Verify debug info contains successful prediction info
        self.assertIn("Prediction successful", self.dashboard.debug_info)

        # Verify history record was created/updated
        history = self.env['predict.revenue.history'].search([
            ('product_id', '=', self.test_product.id),
            ('predict_year', '=', '2025'),
            ('predict_month', '=', '6')
        ])
        self.assertTrue(history)
        self.assertEqual(history.predicted_quantity, 150.0)

    def test_07_missing_required_fields(self):
        """Test behavior when required fields are missing"""
        # Create a test product for this test
        test_product = self.env['product.product'].create({
            'name': 'Test Product for Missing Fields',
            'default_code': 'TESTMISSING',
            'type': 'consu',  # Add the type field
        })

        # Create dashboard with all required fields
        self.env['predict.revenue.dashboard'].create({
            'product_id': test_product.id,
            'predict_year': '2025',  # Required field
            'predict_month': '7',  # Required field
        })

        # Test the behavior when fields are missing in the onchange context
        # We'll use a new record with context to simulate onchange without actually saving
        dashboard_onchange = self.env['predict.revenue.dashboard'].new({
            'product_id': test_product.id,
            # Missing year and month
        })

        # Should return without error when required fields are missing in onchange
        result = dashboard_onchange._onchange_predict_revenue()
        self.assertEqual(result, None)

        # Test with only product_id
        dashboard_partial = self.env['predict.revenue.dashboard'].new({
            'product_id': test_product.id,
            'predict_year': '2025',
            # Missing month
        })

        # Should return without error when some required fields are missing
        result = dashboard_partial._onchange_predict_revenue()
        self.assertEqual(result, None)

    def test_08_update_existing_history(self):
        """Test updating existing history records"""
        # First prediction creates a history record
        self.dashboard._onchange_predict_revenue()

        # Get the initial history record
        initial_history = self.env['predict.revenue.history'].search([
            ('product_id', '=', self.test_product.id),
            ('predict_year', '=', '2025'),
            ('predict_month', '=', '6')
        ])
        self.assertTrue(initial_history)

        # Instead of trying to modify the read-only field directly,
        # we'll create a new mock pipeline that returns a different value
        with mock.patch('joblib.load') as mock_load:
            # Create a new mock pipeline that returns 200.0
            class NewMockModel:
                def predict(self, X):
                    return np.array([200.0])

            class NewMockPipeline:
                def __init__(self):
                    self.named_steps = {
                        'pre': MockPreprocessor(),
                        'lgbm': NewMockModel()
                    }

            # Set the mock to return our new pipeline
            mock_load.return_value = NewMockPipeline()

            # Run prediction again with the new mock
            self.dashboard._onchange_predict_revenue()

        # Verify that the history record was updated, not duplicated
        history_records = self.env['predict.revenue.history'].search([
            ('product_id', '=', self.test_product.id),
            ('predict_year', '=', '2025'),
            ('predict_month', '=', '6')
        ])
        self.assertEqual(len(history_records), 1)

        # The predicted value should be updated in the history
        # Note: We can't check dashboard.predicted_revenue directly since it's read-only
        # and might not reflect the actual value used in the history update
        updated_history = history_records[0]
        self.assertEqual(updated_history.predicted_quantity, 200.0)

    def test_09_edge_cases(self):
        """Test edge cases and special scenarios"""
        # Product with no category
        product_no_categ = self.env['product.product'].create({
            'name': 'No Category Product',
            'default_code': 'NOCAT001',
            'type': 'consu',
            'lst_price': 100.0,
            'standard_price': 50.0,
        })

        dashboard_no_categ = self.env['predict.revenue.dashboard'].create({
            'product_id': product_no_categ.id,
            'predict_year': '2025',
            'predict_month': '6',
        })

        # Should not raise error when product has no category
        dashboard_no_categ._onchange_predict_revenue()
        self.assertEqual(dashboard_no_categ.predicted_revenue, 150.0)

        # Product with no default code
        product_no_code = self.env['product.product'].create({
            'name': 'No Code Product',
            'type': 'consu',
            'lst_price': 100.0,
            'standard_price': 50.0,
        })

        dashboard_no_code = self.env['predict.revenue.dashboard'].create({
            'product_id': product_no_code.id,
            'predict_year': '2025',
            'predict_month': '6',
        })

        # Should not raise error when product has no default code
        dashboard_no_code._onchange_predict_revenue()
        self.assertEqual(dashboard_no_code.predicted_revenue, 150.0)

        # Test with holiday season month
        dashboard_holiday = self.env['predict.revenue.dashboard'].create({
            'product_id': self.test_product.id,
            'predict_year': '2025',
            'predict_month': '12',  # December (holiday season)
        })

        dashboard_holiday._onchange_predict_revenue()
        self.assertEqual(dashboard_holiday.predicted_revenue, 150.0)

    def test_10_new_product_with_no_history(self):
        """Test prediction for new product with no history"""
        new_product = self.env['product.product'].create({
            'name': 'Brand New Product',
            'default_code': 'NEW001',
            'type': 'consu',
            'lst_price': 200.0,
            'standard_price': 100.0,
        })

        dashboard_new = self.env['predict.revenue.dashboard'].create({
            'product_id': new_product.id,
            'predict_year': '2025',
            'predict_month': '6',
        })

        dashboard_new._onchange_predict_revenue()
        self.assertEqual(dashboard_new.predicted_revenue, 150.0)

        # Parse lag values from debug_info
        for line in dashboard_new.debug_info.splitlines():
            if line.startswith("Input data:"):
                input_data = json.loads(line.replace("Input data: ", "").strip().replace("'", '"'))
                break
        else:
            self.fail("Input data not found in debug_info")

        self.assertEqual(input_data[0].get("x_lag_1"), 0.0)
        self.assertEqual(input_data[0].get("x_lag_3_avg"), 0.0)
        self.assertEqual(input_data[0].get("x_lag_6_avg"), 0.0)
        self.assertEqual(input_data[0].get("x_previous_trend"), 0.0)

        # Verify history
        history = self.env['predict.revenue.history'].search([
            ('product_id', '=', new_product.id),
            ('predict_year', '=', '2025'),
            ('predict_month', '=', '6')
        ])
        self.assertTrue(history)
        self.assertEqual(history.predicted_quantity, 150.0)

        # Verify chart
        dashboard_new._compute_chart_data()
        chart_data = json.loads(dashboard_new.chart_data)
        self.assertEqual(len(chart_data['datasets'][0]['data']), 1)
        self.assertEqual(chart_data['datasets'][0]['data'][0], 150.0)

    def test_11_complete_prediction_flow(self):
        """Test the complete prediction flow from start to finish"""
        # Create new dashboard
        dashboard = self.env['predict.revenue.dashboard'].create({
            'product_id': self.test_product.id,
            'predict_year': '2026',
            'predict_month': '3',
        })

        # Run prediction
        dashboard._onchange_predict_revenue()

        # Verify prediction was made
        self.assertEqual(dashboard.predicted_revenue, 150.0)

        # Verify history record was created
        history = self.env['predict.revenue.history'].search([
            ('product_id', '=', self.test_product.id),
            ('predict_year', '=', '2026'),
            ('predict_month', '=', '3')
        ])
        self.assertTrue(history)
        self.assertEqual(history.predicted_quantity, 150.0)

        # Verify chart was updated
        chart_data = json.loads(dashboard.chart_data)
        self.assertTrue(len(chart_data['datasets'][0]['data']) > 0)

        # Run prediction again with the same parameters
        dashboard._onchange_predict_revenue()

        # Should update existing record, not create new one
        history_count = self.env['predict.revenue.history'].search_count([
            ('product_id', '=', self.test_product.id),
            ('predict_year', '=', '2026'),
            ('predict_month', '=', '3')
        ])
        self.assertEqual(history_count, 1)
