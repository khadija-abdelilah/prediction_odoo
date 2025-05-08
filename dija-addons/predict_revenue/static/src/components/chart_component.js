/** @odoo-module **/

import { Component, onMounted, onWillUnmount, useRef, useState } from "@odoo/owl";

/**
 * Enhanced Chart Component for Revenue Prediction
 * Features:
 * - Visualizes predicted product quantities over time
 * - Color-codes bars based on growth/decline
 * - Highlights the most recent prediction
 * - Provides detailed tooltips
 * - Responsive design
 */
export class PredictionChart extends Component {
    static template = "predict_revenue.PredictionChart";
    static props = {
        chartData: { type: String, optional: true },
        readonly: { type: Boolean, optional: true },
        name: { type: String, optional: true },
        record: { type: Object, optional: true },
    };

    setup() {
        this.state = useState({ chart: null });
        this.canvasRef = useRef("canvas");
        this.resizeListener = this.handleResize.bind(this);

        onMounted(() => {
            this.renderChart();
            window.addEventListener('resize', this.resizeListener);
        });

        onWillUnmount(() => {
            window.removeEventListener('resize', this.resizeListener);
            if (this.state.chart) {
                this.state.chart.destroy();
            }
        });
    }

    handleResize() {
        if (this.resizeTimeout) {
            clearTimeout(this.resizeTimeout);
        }

        this.resizeTimeout = setTimeout(() => {
            if (this.state.chart) {
                this.state.chart.resize();
            }
        }, 250);
    }

    getChartData() {
        let chartData;

        try {
            if (this.props.record && this.props.record.data.chart_data) {
                chartData = JSON.parse(this.props.record.data.chart_data);
            } else {
                chartData = {
                    labels: ["01/2025", "02/2025", "03/2025"],
                    datasets: [{
                        label: "Predicted Quantity",
                        data: [120, 150, 180],
                        backgroundColor: [
                            'rgba(75, 192, 192, 0.5)',
                            'rgba(75, 192, 192, 0.5)',
                            'rgba(75, 192, 192, 0.5)'
                        ],
                        borderColor: [
                            'rgba(75, 192, 192, 1)',
                            'rgba(75, 192, 192, 1)',
                            'rgba(75, 192, 192, 1)'
                        ],
                        borderWidth: 1
                    }]
                };
            }

            if (chartData.datasets[0].data.length > 0) {
                const lastIndex = chartData.datasets[0].data.length - 1;

                chartData.datasets.push({
                    label: "Current Prediction",
                    data: Array(lastIndex).fill(null).concat([chartData.datasets[0].data[lastIndex]]),
                    backgroundColor: 'rgba(54, 162, 235, 0.8)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 2,
                    type: 'bar'
                });
            }

            return chartData;
        } catch (error) {
            console.error("Error parsing chart data:", error);
            return {
                labels: ["Error"],
                datasets: [{
                    label: "Data not available",
                    data: [0],
                    backgroundColor: 'rgba(255, 99, 132, 0.5)'
                }]
            };
        }
    }

    renderChart() {
        if (!this.canvasRef.el || !window.Chart) {
            console.warn("Canvas reference or Chart.js not available");
            return;
        }

        const ctx = this.canvasRef.el.getContext("2d");
        const chartData = this.getChartData();

        if (this.state.chart) {
            this.state.chart.destroy();
        }

        this.state.chart = new Chart(ctx, {
            type: "bar",
            data: chartData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                    },
                    tooltip: {
                        callbacks: {
                            title: function (tooltipItems) {
                                return `Period: ${tooltipItems[0].label}`;
                            },
                            label: function (context) {
                                const label = context.dataset.label || '';
                                const value = context.parsed.y || 0;
                                return `${label}: ${value.toFixed(2)} units`;
                            },
                            footer: function (tooltipItems) {
                                const dataIndex = tooltipItems[0].dataIndex;
                                const datasetIndex = tooltipItems[0].datasetIndex;

                                if (datasetIndex !== 0 || dataIndex === 0) {
                                    return null;
                                }

                                const dataset = chartData.datasets[0];
                                const current = dataset.data[dataIndex];
                                const previous = dataset.data[dataIndex - 1];
                                const change = ((current - previous) / previous * 100).toFixed(2);

                                return `Growth: ${change}% compared to previous period`;
                            }
                        }
                    },
                    title: {
                        display: true,
                        text: 'Quantity Forecast by Period',
                        font: {
                            size: 16
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Predicted Quantity'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Period'
                        }
                    }
                },
                animation: {
                    duration: 1000,
                    easing: 'easeOutQuart'
                }
            }
        });
    }
}
