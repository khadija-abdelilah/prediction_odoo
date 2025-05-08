from odoo import models, fields

class PredictRevenueHistory(models.Model):
    _name = 'predict.revenue.history'
    _description = 'Revenue Prediction History'
    _order = 'product_id, predict_year desc, predict_month desc'  # Default sorting

    product_id = fields.Many2one('product.product', string="Product", required=True)
    predict_year = fields.Selection(
        [(str(i), str(i)) for i in range(2025, 2027)], string="Year", required=True
    )
    predict_month = fields.Selection(
        [(str(i), str(i)) for i in range(1, 13)], string="Month", required=True
    )
    predicted_quantity = fields.Float(string="Predicted Quantity", readonly=True)
    prediction_date = fields.Datetime(string="Prediction Date", readonly=True)
