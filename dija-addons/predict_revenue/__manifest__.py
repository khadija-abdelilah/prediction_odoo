{
    'name': 'Smile Prediction',
    'version': '1.0',
    'category': 'Sales',
    'summary': 'Predicts revenue using a machine learning model.',
    'description': 'Predict monthly product order quantities using a trained LightGBM model. Includes automated forecasting, historical tracking, and chart visualization.',
    'author': 'Dija',
    'license': 'LGPL-3',
    'depends': ['sale_management', 'product'],
    'data': [
        'security/ir.model.access.csv',
        'views/predict_revenue_dashboard_view.xml',
        'views/predict_revenue_history_view.xml',
    ],
    'assets': {
        'web.assets_backend': [
            ('include', 'https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js'),
            'predict_revenue/static/src/components/chart_component.js',
            'predict_revenue/static/src/widgets/chart_widget.js',
            'predict_revenue/static/src/scss/chart.scss',
            'predict_revenue/static/src/xml/chart_template.xml',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': True,
}
