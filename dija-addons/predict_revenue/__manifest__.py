# dija-addons/predict_revenue/__manifest__.py
{
    'name': 'Predict Revenue',
    'version': '1.0',
    'category': 'Sales',
    'summary': 'Predicts revenue using a machine learning model.',
    'description': 'Adds a button to sales orders to predict revenue using an external AI API.',
    'author': 'Dija',
    'license': 'LGPL-3',
    'depends': ['sale', 'product',],
    'data': [
        'security/ir.model.access.csv',
        'views/sale_order_view.xml',
        'views/predict_revenue_dashboard_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
