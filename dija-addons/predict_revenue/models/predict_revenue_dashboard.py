from odoo import models, fields, api
from odoo.exceptions import UserError
import requests

class PredictRevenueDashboard(models.Model):
    _name = 'predict.revenue.dashboard'
    _description = 'Dashboard de Prédiction de Revenu'

    product_id = fields.Many2one('product.product', string="Produit", required=True)
    predict_year = fields.Selection(
        [(str(i), str(i)) for i in range(2024, 2031)],
        string="Année", required=True
    )
    predict_month = fields.Selection(
        [(str(i), str(i)) for i in range(1, 13)],
        string="Mois", required=True
    )
    predicted_revenue = fields.Float(string="Revenu Prévu", readonly=True)

    @api.onchange('product_id', 'predict_year', 'predict_month')
    def _onchange_predict_revenue(self):
        """ Automatically call prediction API when fields change """
        if self.product_id and self.predict_year and self.predict_month:
            try:
                payload = {
                    'product': self.product_id.name,
                    'year': int(self.predict_year),
                    'month': int(self.predict_month),
                }
                url = 'http://172.17.0.1:5000/predict'
                response = requests.post(url, json=payload)
                if response.status_code == 200:
                    self.predicted_revenue = response.json().get('predicted_revenue', 0.0)
                else:
                    raise UserError(f"Erreur API : {response.status_code} - {response.text}")
            except Exception as e:
                raise UserError(f"Erreur lors de l’appel API : {str(e)}")
