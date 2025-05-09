# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class PredictRevenueHistory(models.Model):
    _name = 'predict.revenue.history'
    _description = 'Prediction History'
    _order = 'product_id, predict_year desc, predict_month desc'

    product_id = fields.Many2one('product.product', string='Product', required=True)
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

    @api.constrains('predict_year', 'predict_month')
    def _check_date_values(self):
        """Validate predict_year and predict_month values"""
        for record in self:
            # Additional validation if needed beyond the selection field constraints
            if record.predict_year and int(record.predict_year) < 2025:
                raise ValidationError("Year must be 2025 or later")
            if record.predict_month and (int(record.predict_month) < 1 or int(record.predict_month) > 12):
                raise ValidationError("Month must be between 1 and 12")