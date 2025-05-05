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

            // Re-render chart when window is resized
            window.addEventListener('resize', this.resizeListener);
        });

        // Clean up event listener when component is unmounted
        onWillUnmount(() => {
            window.removeEventListener('resize', this.resizeListener);
            if (this.state.chart) {
                this.state.chart.destroy();
            }
        });
    }

    handleResize() {
        // Debounce resize event
        if (this.resizeTimeout) {
            clearTimeout(this.resizeTimeout);
        }

        this.resizeTimeout = setTimeout(() => {
            if (this.state.chart) {
                this.state.chart.resize();
            }
        }, 250);
    }

    /**
     * Parse chart data from the record
     * Falls back to sample data if no data is available
     */
    getChartData() {
        let chartData;

        try {
            // Get chart data from record field
            if (this.props.record && this.props.record.data.chart_data) {
                chartData = JSON.parse(this.props.record.data.chart_data);
            } else {
                // Fallback sample data if no record data available
                chartData = {
                    labels: ["01/2025", "02/2025", "03/2025"],
                    datasets: [{
                        label: "Quantité Prédite",
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

            // Highlight the most recent prediction
            if (chartData.datasets[0].data.length > 0) {
                const lastIndex = chartData.datasets[0].data.length - 1;

                // Create a highlight dataset for the most recent prediction
                chartData.datasets.push({
                    label: "Prédiction Actuelle",
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
                labels: ["Erreur"],
                datasets: [{
                    label: "Données non disponibles",
                    data: [0],
                    backgroundColor: 'rgba(255, 99, 132, 0.5)'
                }]
            };
        }
    }

    /**
     * Render the Chart.js visualization
     */
    renderChart() {
        if (!this.canvasRef.el || !window.Chart) {
            console.warn("Canvas reference or Chart.js not available");
            return;
        }

        const ctx = this.canvasRef.el.getContext("2d");
        const chartData = this.getChartData();

        // Destroy existing chart if it exists
        if (this.state.chart) {
            this.state.chart.destroy();
        }

        // Create the enhanced chart
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
                            title: function(tooltipItems) {
                                return `Période: ${tooltipItems[0].label}`;
                            },
                            label: function(context) {
                                const label = context.dataset.label || '';
                                const value = context.parsed.y || 0;
                                return `${label}: ${value.toFixed(2)} unités`;
                            },
                            footer: function(tooltipItems) {
                                const dataIndex = tooltipItems[0].dataIndex;
                                const datasetIndex = tooltipItems[0].datasetIndex;

                                // Only show growth info for the main dataset
                                if (datasetIndex !== 0 || dataIndex === 0) {
                                    return null;
                                }

                                const dataset = chartData.datasets[0];
                                const current = dataset.data[dataIndex];
                                const previous = dataset.data[dataIndex - 1];
                                const change = ((current - previous) / previous * 100).toFixed(2);

                                return `Évolution: ${change}% par rapport à la période précédente`;
                            }
                        }
                    },
                    title: {
                        display: true,
                        text: 'Prévisions de Quantité par Période',
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
                            text: 'Quantité Prédite'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Période'
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