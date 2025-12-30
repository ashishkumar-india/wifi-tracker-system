/**
 * WiFi Tracker - Charts Module
 */

class ChartsManager {
    constructor() {
        this.activityChart = null;
        this.vendorChart = null;
        this.chartColors = {
            primary: '#6366f1',
            secondary: '#a855f7',
            success: '#10b981',
            warning: '#f59e0b',
            danger: '#ef4444',
            info: '#3b82f6',
            gradientStart: 'rgba(99, 102, 241, 0.3)',
            gradientEnd: 'rgba(99, 102, 241, 0.0)'
        };
    }

    async initCharts() {
        await this.initActivityChart();
        await this.initVendorChart();
    }

    async initActivityChart() {
        const ctx = document.getElementById('activityChart');
        if (!ctx) return;

        try {
            const data = await api.getDeviceHistory(7);

            const gradient = ctx.getContext('2d').createLinearGradient(0, 0, 0, 300);
            gradient.addColorStop(0, this.chartColors.gradientStart);
            gradient.addColorStop(1, this.chartColors.gradientEnd);

            if (this.activityChart) {
                this.activityChart.destroy();
            }

            this.activityChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.history.map(d => this.formatDate(d.date)),
                    datasets: [
                        {
                            label: 'Total Devices',
                            data: data.history.map(d => d.total_devices),
                            borderColor: this.chartColors.primary,
                            backgroundColor: gradient,
                            fill: true,
                            tension: 0.4,
                            pointRadius: 4,
                            pointBackgroundColor: this.chartColors.primary
                        },
                        {
                            label: 'New Devices',
                            data: data.history.map(d => d.new_devices),
                            borderColor: this.chartColors.success,
                            backgroundColor: 'transparent',
                            tension: 0.4,
                            pointRadius: 4,
                            pointBackgroundColor: this.chartColors.success
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'top',
                            labels: {
                                color: '#94a3b8',
                                usePointStyle: true,
                                padding: 20
                            }
                        }
                    },
                    scales: {
                        x: {
                            grid: {
                                color: 'rgba(148, 163, 184, 0.1)'
                            },
                            ticks: {
                                color: '#94a3b8'
                            }
                        },
                        y: {
                            beginAtZero: true,
                            grid: {
                                color: 'rgba(148, 163, 184, 0.1)'
                            },
                            ticks: {
                                color: '#94a3b8'
                            }
                        }
                    }
                }
            });
        } catch (error) {
            console.error('Failed to init activity chart:', error);
        }
    }

    async initVendorChart() {
        const ctx = document.getElementById('vendorChart');
        if (!ctx) return;

        try {
            const stats = await api.getDashboardStats();
            const vendorData = stats.devices_by_vendor || {};

            const labels = Object.keys(vendorData).slice(0, 6);
            const values = labels.map(l => vendorData[l]);

            if (labels.length === 0) {
                labels.push('No Data');
                values.push(1);
            }

            const colors = [
                this.chartColors.primary,
                this.chartColors.secondary,
                this.chartColors.success,
                this.chartColors.warning,
                this.chartColors.info,
                this.chartColors.danger
            ];

            if (this.vendorChart) {
                this.vendorChart.destroy();
            }

            this.vendorChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: labels,
                    datasets: [{
                        data: values,
                        backgroundColor: colors.slice(0, labels.length),
                        borderColor: '#1a1a2e',
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'right',
                            labels: {
                                color: '#94a3b8',
                                usePointStyle: true,
                                padding: 15,
                                font: {
                                    size: 11
                                }
                            }
                        }
                    },
                    cutout: '60%'
                }
            });
        } catch (error) {
            console.error('Failed to init vendor chart:', error);
        }
    }

    formatDate(dateStr) {
        const date = new Date(dateStr);
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    }

    async refresh() {
        await this.initCharts();
    }

    destroy() {
        if (this.activityChart) {
            this.activityChart.destroy();
            this.activityChart = null;
        }
        if (this.vendorChart) {
            this.vendorChart.destroy();
            this.vendorChart = null;
        }
    }
}

const charts = new ChartsManager();
