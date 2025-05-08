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
            'type': 'product',
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

        # Create a mock pipeline
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

        # Create a mock pipeline that the model can load
        class MockPipeline:
            def __init__(self):
                self.named_steps = {
                    'pre': MockPreprocessor(),
                    'lgbm': MockModel()
                }

        pipeline = MockPipeline()

        # Get the model path
        model_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'models',
            'ml_model'
        )

        # Ensure directory exists
        os.makedirs(model_dir, exist_ok=True)

        # Save mock model
        self.model_path = os.path.join(model_dir, 'model_lightgbm_optimized.pkl')
        joblib.dump(pipeline, self.model_path)

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

        # Test chart data with no product selected
        empty_dashboard = self.env['predict.revenue.dashboard'].create({
            'predict_year': '2025',
            'predict_month': '7',
        })
        empty_dashboard.product_id = False
        empty_dashboard._compute_chart_data()

        empty_chart_data = json.loads(empty_dashboard.chart_data)
        self.assertEqual(len(empty_chart_data['datasets'][0]['data']), 0)

    def test_03_onchange_predict_revenue_success(self):
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

    @mock.patch('joblib.load')
    def test_04_model_load_error(self, mock_load):
        """Test error handling when model loading fails"""
        # Make joblib.load raise an exception
        mock_load.side_effect = Exception("Mock loading error")

        # Test that UserError is raised
        with self.assertRaises(UserError) as context:
            self.dashboard._onchange_predict_revenue()

        self.assertIn("Unable to load model", str(context.exception))

    @mock.patch('pandas.DataFrame')
    def test_05_prediction_error(self, mock_df):
        """Test error handling during prediction"""
        # Make DataFrame transformation raise an exception
        mock_df.side_effect = Exception("Mock DataFrame error")

        # Test that UserError is raised
        with self.assertRaises(UserError) as context:
            self.dashboard._onchange_predict_revenue()

        self.assertIn("Erreur de prédiction", str(context.exception))

    def test_06_missing_required_fields(self):
        """Test behavior when required fields are missing"""
        # Create dashboard without a product
        dashboard_no_product = self.env['predict.revenue.dashboard'].create({
            'predict_year': '2025',
            'predict_month': '7',
        })

        # Should return without error when required fields are missing
        result = dashboard_no_product._onchange_predict_revenue()
        self.assertEqual(result, None)

        # Create dashboard without year/month
        dashboard_no_date = self.env['predict.revenue.dashboard'].create({
            'product_id': self.test_product.id,
        })

        # Should return without error when required fields are missing
        result = dashboard_no_date._onchange_predict_revenue()
        self.assertEqual(result, None)

    def test_07_update_existing_history(self):
        """Test updating existing history records"""
        # First prediction creates a history record
        self.dashboard._onchange_predict_revenue()

        # Change the mock model to return a different value
        with mock.patch('numpy.ndarray') as mock_ndarray:
            mock_instance = mock.MagicMock()
            mock_instance.__getitem__.return_value = 200.0
            mock_ndarray.return_value = mock_instance

            # Run prediction again
            with mock.patch.object(type(self.dashboard), 'predicted_revenue', new=200.0):
                self.dashboard._onchange_predict_revenue()

        # Verify that the history record was updated, not duplicated
        history_records = self.env['predict.revenue.history'].search([
            ('product_id', '=', self.test_product.id),
            ('predict_year', '=', '2025'),
            ('predict_month', '=', '6')
        ])
        self.assertEqual(len(history_records), 1)

    def test_08_edge_cases(self):
        """Test edge cases and special scenarios"""
        # Product with no category
        product_no_categ = self.env['product.product'].create({
            'name': 'No Category Product',
            'default_code': 'NOCAT001',
            'type': 'product',
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
            'type': 'product',
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

    def test_09_new_product_with_no_history(self):
        """Test prediction for new product with no history"""
        new_product = self.env['product.product'].create({
            'name': 'Brand New Product',
            'default_code': 'NEW001',
            'type': 'product',
            'lst_price': 200.0,
            'standard_price': 100.0,
        })

        dashboard_new = self.env['predict.revenue.dashboard'].create({
            'product_id': new_product.id,
            'predict_year': '2025',
            'predict_month': '6',
        })

        # Should handle case with no lag values properly
        dashboard_new._onchange_predict_revenue()
        self.assertEqual(dashboard_new.predicted_revenue, 150.0)

        # Verify that lag values defaulted to 0
        self.assertIn("x_lag_1': [0.0]", dashboard_new.debug_info)

    def test_10_complete_prediction_flow(self):
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