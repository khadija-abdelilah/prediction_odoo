import joblib
import pandas as pd
import numpy as np
import os

from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    predict_product_id = fields.Many2one('product.product', string="Produit à Prédire")
    predict_year = fields.Selection(
        [(str(i), str(i)) for i in range(2024, 2031)], string="Année Cible")
    predict_month = fields.Selection(
        [(str(i), str(i)) for i in range(1, 13)], string="Mois Cible")
    predicted_qty = fields.Float(string="Quantité Prédite", readonly=True)

    def predict_button(self):
        for rec in self:
            if rec.predict_product_id and rec.predict_year and rec.predict_month:
                rec.predicted_qty = rec._predict_quantity(
                    rec.predict_product_id,
                    int(rec.predict_year),
                    int(rec.predict_month)
                )

    def _predict_quantity(self, product_id, year, month):
        try:
            # 📂 Chemin vers ton fichier modèle .pkl
            model_path = os.path.join(os.path.dirname(__file__), 'ml_model/best_model_lgbm.pkl')
            model = joblib.load(model_path)
        except Exception as e:
            return 0.0  # retourne 0 si problème avec le modèle

        product = self.env['product.product'].browse(product_id.id)

        sample = pd.DataFrame([{
            'Product': product.default_code or "UNKNOWN",
            'Product Name': product.name,
            'Variant Tags': "Generic",
            'Variant Values': "Standard",
            'YearMonth': f"{year}-{month:02d}",
            'Unit Price': product.lst_price,
            'Sales_Price': product.lst_price,
            'Cost': product.standard_price,
            'Month_Sin': np.sin(2 * np.pi * month / 12),
            'Month_Cos': np.cos(2 * np.pi * month / 12),
            'Lag_1': 1,
            'Lag_3_avg': 1
        }])

        categorical = ["Product", "Product Name", "Variant Tags", "Variant Values", "YearMonth"]
        numerical = ["Unit Price", "Sales_Price", "Cost", "Month_Sin", "Month_Cos", "Lag_1", "Lag_3_avg"]

        try:
            prediction = model.predict(sample[categorical + numerical])
            return float(prediction[0])
        except Exception as e:
            return 0.0  # retourne 0 si erreur de prédiction
