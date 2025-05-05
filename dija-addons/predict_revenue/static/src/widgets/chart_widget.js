/** @odoo-module **/

import { registry } from "@web/core/registry";
import { PredictionChart } from "../components/chart_component";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

/**
 * Field Widget Wrapper for PredictionChart Component
 * Allows using the chart in form views with widget="prediction_chart"
 */
export class PredictionChartField extends PredictionChart {
    static template = PredictionChart.template;
    static props = {
        ...standardFieldProps,
        ...PredictionChart.props,
    };

    setup() {
        super.setup();
        // Field-specific setup if needed in the future
    }
}

// Register the widget in the fields registry
registry.category("fields").add("prediction_chart", {
    component: PredictionChartField,
});