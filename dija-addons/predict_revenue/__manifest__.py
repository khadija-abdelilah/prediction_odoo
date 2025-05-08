{
    'name': 'Predict Revenue',
    'version': '1.0',
    'category': 'Sales',
    'summary': 'Predicts revenue using a machine learning model.',
    'description': 'Adds a button to sales orders to predict revenue using an external AI API.',
    'author': 'Dija',
    'license': 'LGPL-3',
    'depends': ['sale', 'product'],
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
