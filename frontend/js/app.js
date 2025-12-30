/**
 * WiFi Tracker - Main Application
 */

class App {
    constructor() {
        this.currentPage = 'dashboard';
        this.websocket = null;
        this.isScanning = false;
    }

    init() {
        this.setupNavigation();
        this.setupEventListeners();
        this.connectWebSocket();
        this.loadDashboard();
    }

    setupNavigation() {
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const page = item.dataset.page;
                this.navigateTo(page);
            });
        });

        document.querySelectorAll('.view-all').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const page = link.dataset.page;
                this.navigateTo(page);
            });
        });
    }

    setupEventListeners() {
        document.getElementById('scanNowBtn').addEventListener('click', () => {
            this.startQuickScan();
        });

        document.getElementById('startScanBtn').addEventListener('click', () => {
            this.startScan();
        });

        document.getElementById('deviceSearch').addEventListener('input', (e) => {
            devicesManager.search(e.target.value);
        });

        document.getElementById('deviceFilter').addEventListener('change', (e) => {
            const value = e.target.value;
            devicesManager.filters = {};

            if (value === 'online') devicesManager.setFilter('is_online', true);
            else if (value === 'trusted') devicesManager.setFilter('is_trusted', true);
            else if (value === 'suspicious') devicesManager.setFilter('is_suspicious', true);
            else devicesManager.loadDevices();
        });

        document.getElementById('alertFilter').addEventListener('change', (e) => {
            alertsManager.setFilter('alert_type', e.target.value);
        });

        document.getElementById('alertSeverity').addEventListener('change', (e) => {
            alertsManager.setFilter('severity', e.target.value);
        });

        document.getElementById('ackAllBtn').addEventListener('click', () => {
            alertsManager.acknowledgeAll();
        });

        document.getElementById('trainModelsBtn').addEventListener('click', () => {
            this.trainModels();
        });
    }

    navigateTo(page) {
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.toggle('active', item.dataset.page === page);
        });

        document.querySelectorAll('.page').forEach(p => {
            p.classList.toggle('active', p.id === `${page}Page`);
        });

        const titles = {
            dashboard: ['Dashboard', 'Network Security Overview'],
            devices: ['Devices', 'Connected Network Devices'],
            scan: ['Network Scan', 'Discover Devices on Network'],
            alerts: ['Alerts', 'Security Notifications'],
            ml: ['ML Detection', 'Anomaly Detection Models']
        };

        const [title, subtitle] = titles[page] || ['', ''];
        document.getElementById('pageTitle').textContent = title;
        document.querySelector('.header-subtitle').textContent = subtitle;

        this.currentPage = page;
        this.loadPageData(page);
    }

    async loadPageData(page) {
        switch (page) {
            case 'dashboard':
                await this.loadDashboard();
                break;
            case 'devices':
                await devicesManager.loadDevices();
                break;
            case 'scan':
                await this.loadScanStatus();
                break;
            case 'alerts':
                await alertsManager.loadAlerts();
                break;
            case 'ml':
                await this.loadMlStatus();
                break;
        }
    }

    async loadDashboard() {
        try {
            const stats = await api.getDashboardStats();

            document.getElementById('totalDevices').textContent = stats.devices.total;
            document.getElementById('onlineDevices').textContent = stats.devices.online;
            document.getElementById('alertsCount').textContent = stats.alerts.unacknowledged;
            document.getElementById('suspiciousCount').textContent = stats.devices.suspicious;

            devicesManager.updateDeviceCount(stats.devices.total);
            alertsManager.updateAlertCount(stats.alerts.unacknowledged);

            await charts.initCharts();
            await this.loadRecentActivity();

        } catch (error) {
            console.error('Failed to load dashboard:', error);
            this.showToast('Failed to load dashboard data', 'error');
        }
    }

    async loadRecentActivity() {
        const list = document.getElementById('activityList');

        try {
            const data = await api.getActivityTimeline(24);

            if (data.timeline.length === 0) {
                list.innerHTML = '<p class="no-data">No recent activity</p>';
                return;
            }

            list.innerHTML = data.timeline.slice(0, 10).map(activity => `
                <div class="activity-item">
                    <div class="activity-icon ${this.getActivityIcon(activity.event_type)}">
                        ${this.getActivitySvg(activity.event_type)}
                    </div>
                    <div class="activity-details">
                        <div class="activity-title">${this.formatEventType(activity.event_type)}</div>
                        <div class="activity-subtitle">
                            ${activity.device_hostname || activity.device_mac || 'Unknown device'}
                            ${activity.new_value ? ` - ${activity.new_value}` : ''}
                        </div>
                    </div>
                    <span class="activity-time">${this.formatTime(activity.timestamp)}</span>
                </div>
            `).join('');

        } catch (error) {
            console.error('Failed to load activity:', error);
            list.innerHTML = '<p class="error">Failed to load activity</p>';
        }
    }

    async loadScanStatus() {
        try {
            const status = await api.getScanStatus();

            const badge = document.getElementById('scanStatusBadge');
            badge.textContent = status.is_scanning ? 'Scanning...' : 'Idle';
            badge.className = `badge ${status.is_scanning ? 'badge-warning' : ''}`;

            const progress = document.getElementById('scanProgress');
            progress.classList.toggle('hidden', !status.is_scanning);

            const results = document.getElementById('scanResults');
            if (status.last_scan_time) {
                results.innerHTML = `<p>Last scan: ${this.formatTime(status.last_scan_time)}</p>`;
            }

            const networkInfo = await api.getNetworkInfo();
            document.getElementById('networkRange').placeholder = networkInfo.network_range || '192.168.1.0/24';

        } catch (error) {
            console.error('Failed to load scan status:', error);
        }
    }

    async loadMlStatus() {
        const container = document.getElementById('mlModelsStatus');

        try {
            const status = await api.getMlStatus();

            container.innerHTML = `
                <div class="ml-model-card">
                    <div class="ml-model-header">
                        <span class="ml-model-name">Isolation Forest</span>
                        <span class="ml-model-status ${status.isolation_forest.trained ? 'trained' : 'untrained'}">
                            ${status.isolation_forest.trained ? 'Trained' : 'Not Trained'}
                        </span>
                    </div>
                    <p>Unsupervised anomaly detection using decision trees</p>
                </div>
                <div class="ml-model-card">
                    <div class="ml-model-header">
                        <span class="ml-model-name">Autoencoder</span>
                        <span class="ml-model-status ${status.autoencoder.trained ? 'trained' : 'untrained'}">
                            ${status.autoencoder.available ? (status.autoencoder.trained ? 'Trained' : 'Not Trained') : 'Unavailable'}
                        </span>
                    </div>
                    <p>Deep learning model using reconstruction error</p>
                </div>
            `;

            document.getElementById('trainModelsBtn').disabled = !auth.isAdmin();

        } catch (error) {
            console.error('Failed to load ML status:', error);
            container.innerHTML = '<p class="error">Failed to load ML status</p>';
        }
    }

    async startQuickScan() {
        await this.performScan({ scanType: 'arp' });
    }

    async startScan() {
        let networkRange = document.getElementById('networkRange').value.trim() || null;
        const scanType = document.getElementById('scanType').value;

        // Validate and fix network range format
        if (networkRange) {
            const cidrPattern = /^(\d{1,3}\.){3}\d{1,3}\/\d{1,2}$/;
            const ipPattern = /^(\d{1,3}\.){3}\d{1,3}$/;

            if (cidrPattern.test(networkRange)) {
                // Valid CIDR format, use as-is
            } else if (ipPattern.test(networkRange)) {
                // Single IP - convert to /24 network
                const parts = networkRange.split('.');
                networkRange = `${parts[0]}.${parts[1]}.${parts[2]}.0/24`;
                this.showToast(`Using network range: ${networkRange}`, 'info');
            } else {
                this.showToast('Invalid network range format. Use format: 192.168.1.0/24', 'error');
                return;
            }
        }

        await this.performScan({ networkRange, scanType });
    }

    async performScan(options) {
        if (this.isScanning) {
            this.showToast('Scan already in progress', 'warning');
            return;
        }

        try {
            this.isScanning = true;
            this.showToast('Starting network scan...', 'info');

            const session = await api.startScan(options);

            document.getElementById('scanProgress').classList.remove('hidden');
            document.getElementById('scanStatusBadge').textContent = 'Scanning...';
            document.getElementById('scanStatusBadge').classList.add('badge-warning');

        } catch (error) {
            console.error('Failed to start scan:', error);
            const errorMessage = typeof error === 'object'
                ? (error.message || error.detail || JSON.stringify(error))
                : String(error);
            this.showToast(errorMessage || 'Failed to start scan', 'error');
            this.isScanning = false;
        }
    }

    async trainModels() {
        const btn = document.getElementById('trainModelsBtn');
        const results = document.getElementById('trainingResults');

        btn.disabled = true;
        btn.innerHTML = '<span>Training...</span>';
        results.innerHTML = '<div class="loading-spinner">Training models...</div>';

        try {
            const result = await api.trainModels();

            if (result.status === 'insufficient_data') {
                results.innerHTML = `
                    <div class="alert alert-warning">
                        Insufficient data for training. Need at least ${result.required} samples, 
                        but only have ${result.samples}.
                    </div>
                `;
            } else {
                results.innerHTML = `
                    <div class="alert alert-success">
                        Training complete! Trained on ${result.total_samples} samples.
                    </div>
                `;
                await this.loadMlStatus();
            }

            this.showToast('Model training complete', 'success');

        } catch (error) {
            console.error('Training failed:', error);
            results.innerHTML = `<div class="alert alert-error">Training failed: ${error.message}</div>`;
            this.showToast('Training failed', 'error');
        }

        btn.disabled = false;
        btn.innerHTML = '<span>Train Models</span>';
    }

    connectWebSocket() {
        const wsUrl = 'ws://localhost:8000/ws/live';

        try {
            this.websocket = new WebSocket(wsUrl);

            this.websocket.onopen = () => {
                console.log('WebSocket connected');
                this.updateConnectionStatus('connected');
            };

            this.websocket.onclose = () => {
                console.log('WebSocket disconnected');
                this.updateConnectionStatus('disconnected');
                setTimeout(() => this.connectWebSocket(), 5000);
            };

            this.websocket.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.updateConnectionStatus('disconnected');
            };

            this.websocket.onmessage = (event) => {
                this.handleWebSocketMessage(JSON.parse(event.data));
            };

        } catch (error) {
            console.error('Failed to connect WebSocket:', error);
            this.updateConnectionStatus('disconnected');
        }
    }

    handleWebSocketMessage(message) {
        console.log('WebSocket message:', message);

        switch (message.type) {
            case 'alert':
                this.handleNewAlert(message.data);
                break;
            case 'device_update':
                this.handleDeviceUpdate(message.data, message.event);
                break;
            case 'scan_update':
                this.handleScanUpdate(message.data);
                break;
        }
    }

    handleNewAlert(alert) {
        this.showToast(alert.message, 'warning');

        const count = parseInt(document.getElementById('alertCount').textContent) + 1;
        alertsManager.updateAlertCount(count);

        if (this.currentPage === 'alerts') {
            alertsManager.loadAlerts();
        }
    }

    handleDeviceUpdate(device, event) {
        if (event === 'discovered') {
            const count = parseInt(document.getElementById('totalDevices').textContent) + 1;
            document.getElementById('totalDevices').textContent = count;
        }

        if (this.currentPage === 'devices') {
            devicesManager.loadDevices();
        }
    }

    handleScanUpdate(data) {
        if (data.status === 'completed' || data.status === 'failed') {
            this.isScanning = false;
            document.getElementById('scanProgress').classList.add('hidden');
            document.getElementById('scanStatusBadge').textContent = 'Idle';
            document.getElementById('scanStatusBadge').classList.remove('badge-warning');

            if (data.status === 'completed') {
                this.showToast(
                    `Scan complete: ${data.total_devices} devices found, ${data.new_devices} new`,
                    'success'
                );
                this.loadDashboard();
            } else {
                this.showToast(`Scan failed: ${data.error}`, 'error');
            }
        }
    }

    updateConnectionStatus(status) {
        const el = document.getElementById('wsStatus');
        el.className = `connection-status ${status}`;
        el.querySelector('span:last-child').textContent =
            status === 'connected' ? 'Connected' : 'Disconnected';
    }

    getActivityIcon(type) {
        switch (type) {
            case 'connected': return 'new';
            case 'disconnected': return 'info';
            case 'ip_changed': return 'alert';
            default: return 'info';
        }
    }

    getActivitySvg(type) {
        switch (type) {
            case 'connected':
                return '<svg width="16" height="16" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"/></svg>';
            case 'disconnected':
                return '<svg width="16" height="16" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"/></svg>';
            default:
                return '<svg width="16" height="16" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"/></svg>';
        }
    }

    formatEventType(type) {
        return type.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
    }

    formatTime(isoString) {
        if (!isoString) return '';
        const date = new Date(isoString);
        const now = new Date();
        const diff = now - date;

        if (diff < 60000) return 'Just now';
        if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
        if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;

        return date.toLocaleDateString();
    }

    showToast(message, type = 'info') {
        const container = document.getElementById('toastContainer');

        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <span class="toast-message">${message}</span>
            <button class="toast-close" onclick="this.parentElement.remove()">
                <svg width="16" height="16" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"/>
                </svg>
            </button>
        `;

        container.appendChild(toast);

        setTimeout(() => {
            toast.remove();
        }, 5000);
    }
}

window.app = new App();
