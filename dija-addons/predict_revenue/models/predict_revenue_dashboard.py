# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError

import os
import pandas as pd
import numpy as np
import joblib
import warnings

class PredictRevenueDashboard(models.Model):
    _name = 'predict.revenue.dashboard'
    _description = 'Dashboard de Prédiction de Revenu'

    product_id = fields.Many2one('product.product', string="Produit", required=True)
    predict_year = fields.Selection(
        [(str(i), str(i)) for i in range(2025, 2027)], string="Année", required=True
    )
    predict_month = fields.Selection(
        [(str(i), str(i)) for i in range(1, 13)], string="Mois", required=True
    )
    predicted_revenue = fields.Float(string="Quantité Prédite", readonly=True)

    @api.onchange('product_id', 'predict_year', 'predict_month')
    def _onchange_predict_revenue(self):
        if self.product_id and self.predict_year and self.predict_month:
            try:
                # Load model
                model_path = os.path.join(os.path.dirname(__file__), 'ml_model/model_lgbm.pkl')
                pipeline = joblib.load(model_path)

                # Date features
                month = int(self.predict_month)
                year = int(self.predict_year)
                quarter = (month - 1) // 3 + 1

                # Construct sample input with proper values
                sample_data = {
                    'Product': self.product_id.name,
                    'Product Name': self.product_id.name,
                    'Variant Tags': 'Generic',
                    'Variant Values': 'Standard',
                    'Customer': 'Unknown',
                    'Salesperson': 'Unknown',
                    'YearMonth': f"{year}-{month:02d}",
                    'Quarter': f"Q{quarter}",
                    'Unit Price': self.product_id.lst_price,
                    'Sales_Price': self.product_id.lst_price,
                    'Cost': self.product_id.standard_price,
                    'Month_Sin': np.sin(2 * np.pi * month / 12),
                    'Month_Cos': np.cos(2 * np.pi * month / 12),
                    'Lag_1': 1.0,
                    'Lag_3_avg': 1.0
                }

                sample = pd.DataFrame([sample_data])

                # Enforce feature column order
                expected_columns = pipeline.feature_names_in_
                sample = sample.reindex(columns=expected_columns)

                # Optional: fill any missing values
                sample = sample.fillna(0)

                # Make prediction while suppressing harmless warnings
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", UserWarning)
                    prediction = pipeline.predict(sample)

                self.predicted_revenue = float(prediction[0])

            except Exception as e:
                raise UserError(f"Erreur prédiction locale : {str(e)}")
