from flask import Flask, request, jsonify
import joblib
import pandas as pd
import numpy as np
import os

app = Flask(__name__)

# Load the model
model_path = os.path.join(os.path.dirname(__file__), 'best_model_lgbm.pkl')
model = joblib.load(model_path)

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json()

        product = data.get('product')
        year = data.get('year')
        month = data.get('month')

        # Calculate dummy Quarter
        if month in [1, 2, 3]:
            quarter = "Q1"
        elif month in [4, 5, 6]:
            quarter = "Q2"
        elif month in [7, 8, 9]:
            quarter = "Q3"
        else:
            quarter = "Q4"

        # Prepare input dataframe
        sample = pd.DataFrame([{
            'Product': product,
            'Product Name': product,
            'Variant Tags': "Generic",
            'Variant Values': "Standard",
            'YearMonth': f"{year}-{month:02d}",
            'Unit Price': 10.0,       # Dummy price
            'Sales_Price': 10.0,       # Dummy sales price
            'Cost': 5.0,               # Dummy cost
            'Month_Sin': np.sin(2 * np.pi * month / 12),
            'Month_Cos': np.cos(2 * np.pi * month / 12),
            'Lag_1': 1,
            'Lag_3_avg': 1,
            'Customer': "Unknown",
            'Quarter': quarter,
            'Salesperson': "Unknown"
        }])

        prediction = model.predict(sample)
        predicted_revenue = float(prediction[0])

        return jsonify({'predicted_revenue': predicted_revenue})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
