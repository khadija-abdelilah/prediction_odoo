# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError

import os
import pandas as pd
import numpy as np
import joblib
import warnings
import json
import logging

_logger = logging.getLogger(__name__)


class PredictRevenueDashboard(models.Model):
    _name = 'predict.revenue.dashboard'
    _description = 'Revenue Prediction Dashboard'

    product_id = fields.Many2one('product.product', string='Product', required=True)
    predict_year = fields.Selection(
        [(str(i), str(i)) for i in range(2025, 2027)],
        string='Year', required=True
    )
    predict_month = fields.Selection(
        [(str(i), str(i)) for i in range(1, 13)],
        string='Month', required=True
    )
    predicted_revenue = fields.Float(string='Predicted Quantity', readonly=True)
    debug_info = fields.Text(string='Debug Information', readonly=True)

    chart_data = fields.Text(
        string='Données du Graphique',
        compute='_compute_chart_data',
        readonly=True
    )
    chart_dummy = fields.Char(
        string='Graphique',
        compute='_compute_chart_dummy'
    )

    @api.depends('chart_data')
    def _compute_chart_dummy(self):
        for rec in self:
            rec.chart_dummy = 'display'

    @api.depends('product_id')
    def _compute_chart_data(self):
        for rec in self:
            data = {'labels': [], 'datasets': [{
                'label': 'Predicted Quantity',
                'data': [], 'backgroundColor': [], 'borderColor': []
            }]}
            if rec.product_id:
                hist = self.env['predict.revenue.history'].search(
                    [('product_id', '=', rec.product_id.id)],
                    order='predict_year desc, predict_month desc', limit=6
                )
                prev = None
                for h in reversed(hist):
                    val = h.predicted_quantity
                    data['labels'].append(f"{h.predict_month}/{h.predict_year}")
                    data['datasets'][0]['data'].append(val)
                    if prev is None or val >= prev:
                        bg, br = 'rgba(75,192,192,0.5)', 'rgba(75,192,192,1)'
                    else:
                        bg, br = 'rgba(255,99,132,0.5)', 'rgba(255,99,132,1)'
                    data['datasets'][0]['backgroundColor'].append(bg)
                    data['datasets'][0]['borderColor'].append(br)
                    prev = val
            rec.chart_data = json.dumps(data)

    @api.onchange('product_id', 'predict_year', 'predict_month')
    def _onchange_predict_revenue(self):
        if not (self.product_id and self.predict_year and self.predict_month):
            return

        # 1. Charger le pipeline
        model_path = os.path.join(
            os.path.dirname(__file__), 'ml_model', 'model_lightgbm_optimized.pkl'
        )
        try:
            pipe = joblib.load(model_path)
            _logger.info("ML model loaded successfully")
        except Exception as e:
            _logger.error(f"Model load error: {e}")
            raise UserError(f"Unable to load model : {e}")

        # 2. Date cible
        year = int(self.predict_year)
        month = int(self.predict_month)

        # 3. Caractéristiques statiques du produit
        prod = self.product_id
        default_code = prod.default_code or ''
        categ_id = prod.categ_id.id if prod.categ_id else 0
        # Récupérer le chemin complet de la catégorie
        categ_path = ""
        if prod.categ_id:
            category = prod.categ_id
            categ_path = category.complete_name if hasattr(category, 'complete_name') else category.name

        prod_type = prod.type or 'product'
        list_price = float(prod.lst_price or 0.0)
        standard_price = float(prod.standard_price or 0.0)

        # 4. Features temporelles
        month_sin = float(np.sin(2 * np.pi * month / 12))
        month_cos = float(np.cos(2 * np.pi * month / 12))
        is_holiday = 1 if month in (11, 12, 1) else 0
        discount_rate = 0.0

        # 5. Lags depuis l'historique existant
        History = self.env['predict.revenue.history']
        hist = History.search(
            [('product_id', '=', prod.id)],
            order='predict_year desc, predict_month desc'
        )
        hist_vals = [h.predicted_quantity for h in hist]
        lag_1 = float(hist_vals[0]) if hist_vals else 0.0
        lag_3_avg = float(np.mean(hist_vals[:3])) if len(hist_vals) >= 3 else lag_1
        lag_6_avg = float(np.mean(hist_vals[:6])) if len(hist_vals) >= 6 else lag_3_avg
        prev_trend = float(hist_vals[0] - hist_vals[1]) if len(hist_vals) >= 2 else 0.0

        # 6. Approche avec DataFrame et noms de caractéristiques exacts
        try:
            # Récupérer le préprocesseur et le modèle
            preprocessor = pipe.named_steps['pre']
            model = pipe.named_steps['lgbm']

            # D'abord on crée un DataFrame de base avec les noms exacts que le modèle attend
            input_data = {
                'default_code': [default_code],
                'categ_id/id': [categ_path],  # Utiliser le chemin complet
                'type': [prod_type],
                'list_price': [list_price],
                'standard_price': [standard_price],
                'Month': [month],
                'Year': [year],
                'x_month_sin': [month_sin],
                'x_month_cos': [month_cos],
                'x_lag_1': [lag_1],
                'x_lag_3_avg': [lag_3_avg],
                'x_lag_6_avg': [lag_6_avg],
                'x_previous_trend': [prev_trend],
                'x_is_holiday_season': [is_holiday],
                'x_discount_rate': [discount_rate]
            }

            df_input = pd.DataFrame(input_data)

            # Debug information
            debug_info = []
            debug_info.append(f"Input DataFrame shape: {df_input.shape}")
            debug_info.append(f"Input DataFrame columns: {df_input.columns.tolist()}")
            debug_info.append(f"Input DataFrame types: {df_input.dtypes.to_dict()}")
            debug_info.append(f"Input data: {df_input.to_dict(orient='records')}")

            # Vérifier si les colonnes numériques contiennent des NaN et les remplacer par 0
            numeric_cols = ['list_price', 'standard_price', 'Month', 'Year',
                            'x_month_sin', 'x_month_cos', 'x_lag_1', 'x_lag_3_avg',
                            'x_lag_6_avg', 'x_previous_trend', 'x_is_holiday_season', 'x_discount_rate']

            for col in numeric_cols:
                if col in df_input.columns:
                    # Convertir explicitement en float pour éviter les problèmes de type
                    df_input[col] = pd.to_numeric(df_input[col], errors='coerce').fillna(0.0).astype(float)

            # Appliquer le préprocesseur directement sur le DataFrame
            X_transformed = preprocessor.transform(df_input)
            debug_info.append(f"Transformed shape: {X_transformed.shape}")

            # Faire la prédiction
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', UserWarning)
                pred = model.predict(X_transformed)[0]

            self.predicted_revenue = float(pred)
            debug_info.append(f"Prediction successful: {pred}")

            # Mettre à jour les infos de debug
            self.debug_info = "\n".join(debug_info)

        except Exception as e:
            error_msg = f"Erreur de prédiction: {e}\n"

            # Tracer l'exception complète pour plus d'informations
            import traceback
            error_details = traceback.format_exc()
            _logger.error(f"Error details: {error_details}")

            # Essayer de récupérer des informations sur le modèle pour aider au debug
            try:
                # Récupérer les noms de colonnes attendus s'ils sont disponibles
                expected_features = []
                for _, transformer, cols in preprocessor.transformers_:
                    if hasattr(transformer, 'get_feature_names_out'):
                        expected_features.extend(transformer.get_feature_names_out(cols))
                    elif hasattr(transformer, 'categories_'):
                        for i, category in enumerate(transformer.categories_):
                            for cat in category:
                                expected_features.append(f"{cols[i]}_{cat}")
                    else:
                        expected_features.extend(cols)

                error_msg += f"Caractéristiques attendues: {expected_features}\n"

                # Afficher un exemple de données d'entrée
                error_msg += f"Input data: {df_input.to_dict(orient='records')}\n"
            except Exception as e2:
                error_msg += f"Model introspection error: {e2}\n"

            # Enregistrer les informations de debug
            self.debug_info = error_msg + "\n" + error_details
            raise UserError(error_msg)

        # 7. Enregistrer l'historique
        vals = {
            'product_id': prod.id,
            'predict_year': self.predict_year,
            'predict_month': self.predict_month,
            'predicted_quantity': self.predicted_revenue,
            'prediction_date': fields.Datetime.now()
        }
        existing = History.search([
            ('product_id', '=', prod.id),
            ('predict_year', '=', self.predict_year),
            ('predict_month', '=', self.predict_month)
        ], limit=1)
        if existing:
            existing.write(vals)
        else:
            History.create(vals)

        # 8. Rafraîchir le courbe
        self._compute_chart_data()
        self._compute_chart_dummy()


class PredictRevenueHistory(models.Model):
    _name = 'predict.revenue.history'
    _description = 'Prediction History'
    _order = 'product_id, predict_year desc, predict_month desc'

    product_id = fields.Many2one('product.product', string='Produit', required=True)
    predict_year = fields.Selection(
        [(str(i), str(i)) for i in range(2025, 2027)],
        string='Year', required=True
    )
    predict_month = fields.Selection(
        [(str(i), str(i)) for i in range(1, 13)],
        string='Month', required=True
    )
    predicted_quantity = fields.Float(string='Predicted Quantity', readonly=True)
    prediction_date = fields.Datetime(string='Prediction Date', readonly=True)
