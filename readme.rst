.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License: AGPL-3

.. |badge2| image:: https://img.shields.io/badge/github-Smile--SA%2Fodoo_addons-lightgray.png?logo=github
    :target: https://github.com/Smile-SA/odoo_addons/tree/18.0/smile_prediction
    :alt: Smile-SA/odoo_addons

|badge1| |badge2|

======================
Smile Prediction
======================

This module provides advanced demand forecasting capabilities using machine learning to predict **future product order quantities**.

The prediction system is based on a trained LightGBM model that analyzes historical sales and product features to forecast monthly demand per product.

Key features of this module include:

- Quantity prediction dashboard for visualizing forecasts
- Historical tracking of all predictions
- Interactive charts showing trends in predicted demand
- Machine learning integration with Odoo's product catalog
- Support for seasonality, promotions, and product characteristics

.. contents:: Table of contents
   :local:

Usage
=====

The Smile Prediction module allows you to forecast future product **quantities** in just a few steps:

1. Navigate to the Prediction Dashboard:

   .. image:: static/description/dashboard_menu.png
      :alt: Navigate to dashboard
      :width: 850px

2. Select a product you want to predict:

   .. image:: static/description/select_product.png
      :alt: Select product
      :width: 850px

3. Choose the year and month of prediction:

   .. image:: static/description/select_period.png
      :alt: Select period
      :width: 850px

4. The system generates a predicted quantity based on your selection:

   .. image:: static/description/prediction_result.png
      :alt: Prediction result
      :width: 850px

5. Review the historical prediction chart:

   .. image:: static/description/prediction_chart.png
      :alt: Prediction chart
      :width: 850px

6. Access detailed prediction logs:

   .. image:: static/description/prediction_history.png
      :alt: Prediction history
      :width: 850px

Technical Details
=================

The forecasting engine relies on a machine learning pipeline:

- Trained LightGBM model optimized for demand prediction
- Feature engineering:
  - Product data (category, pricing, type)
  - Temporal variables (month, year, seasonality)
  - Historical lags (1, 3, 6 months, trends)
  - Special event indicators (holiday season, discounts)
- Automatic prediction via onchange mechanism
- History storage and graphical output

Known issues
============

- Predictions may be less accurate for products with no or very limited historical data.
- The model should be periodically retrained with updated data to maintain accuracy.

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/Smile-SA/odoo_addons/issues>`_.
If you encounter an issue, please report it with detailed steps
`here <https://github.com/Smile-SA/odoo_addons/issues/new?body=module:%20smile_prediction%0Aversion:%2018.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.

Do not contact contributors directly for support.

Credits
=======

Contributors
------------

* Smile SA Development Team
* Khadija ABDELILAH

Maintainer
----------

This module is maintained by Smile SA.

Since 1991, Smile has been a pioneer in open technologies and the leading European expert in open-source enterprise solutions.
