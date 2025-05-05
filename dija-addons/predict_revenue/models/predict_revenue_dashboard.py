# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError

import os
import pandas as pd
import numpy as np
import joblib
import warnings
import json

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

    # Keeps the chart data JSON
    chart_data = fields.Text(
        string="Données du Graphique",
        compute='_compute_chart_data',
        help="JSON pour le graphique",
        readonly=True
    )

    # Dummy Char field for widget rendering
    chart_dummy = fields.Char(
        string="Graphique",
        compute="_compute_chart_dummy",
        help="Champ utilisé pour afficher le graphique"
    )

    @api.depends('chart_data')
    def _compute_chart_dummy(self):
        for rec in self:
            # Dummy content triggers the widget – actual data is in chart_data
            rec.chart_dummy = "display"

    @api.depends('product_id')
    def _compute_chart_data(self):
        for record in self:
            data = {
                'labels': [],
                'datasets': [{
                    'label': 'Quantité Prédite',
                    'data': [],
                    'backgroundColor': [],
                    'borderColor': []
                }]
            }
            if record.product_id:
                history = self.env['predict.revenue.history'].search([
                    ('product_id', '=', record.product_id.id)
                ], order='predict_year desc, predict_month desc', limit=6)

                prev = None
                for h in reversed(history):
                    data['labels'].append(f"{h.predict_month}/{h.predict_year}")
                    data['datasets'][0]['data'].append(h.predicted_quantity)

                    if prev is None or h.predicted_quantity >= prev:
                        bg = 'rgba(75, 192, 192, 0.5)'
                        br = 'rgba(75, 192, 192, 1)'
                    else:
                        bg = 'rgba(255, 99, 132, 0.5)'
                        br = 'rgba(255, 99, 132, 1)'

                    data['datasets'][0]['backgroundColor'].append(bg)
                    data['datasets'][0]['borderColor'].append(br)
                    prev = h.predicted_quantity

            record.chart_data = json.dumps(data)

    @api.onchange('product_id', 'predict_year', 'predict_month')
    def _onchange_predict_revenue(self):
        if self.product_id and self.predict_year and self.predict_month:
            try:
                model_path = os.path.join(os.path.dirname(__file__), 'ml_model/model_lgbm.pkl')
                pipeline = joblib.load(model_path)
                month = int(self.predict_month)
                year = int(self.predict_year)
                quarter = (month - 1) // 3 + 1

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
                sample = sample.reindex(columns=pipeline.feature_names_in_).fillna(0)

                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", UserWarning)
                    prediction = pipeline.predict(sample)

                predicted_quantity = float(prediction[0])
                self.predicted_revenue = predicted_quantity

                history_model = self.env['predict.revenue.history']
                existing = history_model.search([
                    ('product_id', '=', self.product_id.id),
                    ('predict_year', '=', self.predict_year),
                    ('predict_month', '=', self.predict_month)
                ], limit=1)

                if existing:
                    existing.write({
                        'predicted_quantity': predicted_quantity,
                        'prediction_date': fields.Datetime.now()
                    })
                else:
                    history_model.create({
                        'product_id': self.product_id.id,
                        'predict_year': self.predict_year,
                        'predict_month': self.predict_month,
                        'predicted_quantity': predicted_quantity,
                        'prediction_date': fields.Datetime.now()
                    })

                # Recompute chart JSON and widget field
                self._compute_chart_data()
                self._compute_chart_dummy()

            except Exception as e:
                raise UserError(f"Erreur prédiction locale : {str(e)}")
