import pandas as pd
import numpy as np
import os
import joblib
from flask import Flask, request, jsonify

app = Flask(__name__)

# Charger le modèle
model_path = os.path.join(os.path.dirname(__file__), 'best_model_lgbm.pkl')
model = joblib.load(model_path)

# Charger les données de référence
reference_data_path = os.path.join(os.path.dirname(__file__), 'final_orders_cleaned_ready_for_model_augmented.csv')
reference_data = pd.read_csv(reference_data_path)

# Extraire Year et Month à partir de 'Order Date'
reference_data['Order Date'] = pd.to_datetime(reference_data['Order Date'])  # Convertir en datetime
reference_data['Year'] = reference_data['Order Date'].dt.year
reference_data['Month'] = reference_data['Order Date'].dt.month
reference_data['YearMonth'] = reference_data['Year'].astype(str) + '-' + reference_data['Month'].astype(str).str.zfill(2)

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json()

        product = data.get('product')
        year = int(data.get('year'))
        month = int(data.get('month'))

        # Préparer YearMonth
        year_month = f"{year}-{str(month).zfill(2)}"

        # Chercher une vraie ligne dans le dataset
        match = reference_data[
            (reference_data['Product Name'] == product) &
            (reference_data['YearMonth'] == year_month)
        ]

        if match.empty:
            return jsonify({'error': 'No matching product and date found in reference data'}), 404

        # Prendre la première ligne trouvée
        match_row = match.iloc[0]

        # Construire l'échantillon pour prédiction
        sample = pd.DataFrame([{
            'Product': match_row['Internal Reference'],
            'Product Name': match_row['Product Name'],
            'Variant Tags': match_row['Variant Tags'],
            'Variant Values': match_row['Variant Values'],
            'YearMonth': year_month,
            'Unit Price': match_row['Unit Price'],
            'Sales_Price': match_row['Sales Price'],
            'Cost': match_row['Cost_y'],
            'Month_Sin': np.sin(2 * np.pi * month / 12),
            'Month_Cos': np.cos(2 * np.pi * month / 12),
            'Lag_1': 1,
            'Lag_3_avg': 1,
            'Customer': match_row['Customer'],
            'Quarter': f"Q{((month-1)//3)+1}",
            'Salesperson': match_row['Salesperson'],
        }])

        prediction = model.predict(sample)
        predicted_revenue = float(prediction[0])

        return jsonify({'predicted_revenue': predicted_revenue})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
