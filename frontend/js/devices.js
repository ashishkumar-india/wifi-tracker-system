/**
 * WiFi Tracker - Devices Module
 */

class DevicesManager {
    constructor() {
        this.devices = [];
        this.currentPage = 1;
        this.pageSize = 20;
        this.filters = {};
    }

    async loadDevices() {
        const grid = document.getElementById('devicesGrid');
        grid.innerHTML = '<div class="loading-spinner">Loading devices...</div>';

        try {
            const response = await api.getDevices(this.currentPage, this.pageSize, this.filters);
            this.devices = response.devices;
            this.renderDevices();
            this.updateDeviceCount(response.total);
        } catch (error) {
            console.error('Failed to load devices:', error);
            grid.innerHTML = '<p class="error">Failed to load devices</p>';
        }
    }

    renderDevices() {
        const grid = document.getElementById('devicesGrid');

        if (this.devices.length === 0) {
            grid.innerHTML = '<p class="no-data">No devices found</p>';
            return;
        }

        grid.innerHTML = this.devices.map(device => this.renderDeviceCard(device)).join('');

        grid.querySelectorAll('.device-card').forEach(card => {
            card.addEventListener('click', (e) => {
                if (!e.target.closest('.device-actions')) {
                    this.showDeviceDetails(card.dataset.id);
                }
            });
        });

        grid.querySelectorAll('.btn-trust').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.toggleTrust(btn.dataset.id);
            });
        });

        grid.querySelectorAll('.btn-analyze').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.analyzeDevice(btn.dataset.id);
            });
        });
    }

    renderDeviceCard(device) {
        const statusClass = device.is_online ? 'online' : 'offline';
        const cardClass = device.is_suspicious ? 'suspicious' : statusClass;

        return `
            <div class="device-card ${cardClass}" data-id="${device.id}">
                <div class="device-header">
                    <div>
                        <div class="device-name">${device.hostname || 'Unknown Device'}</div>
                        <div class="device-mac">${device.mac_address}</div>
                    </div>
                    <span class="device-status ${statusClass}">${device.is_online ? 'Online' : 'Offline'}</span>
                </div>
                <div class="device-info">
                    ${device.vendor ? `<span><strong>Vendor:</strong> ${device.vendor}</span>` : ''}
                    ${device.device_type ? `<span><strong>Type:</strong> ${device.device_type}</span>` : ''}
                    ${device.latest_scan ? `<span><strong>IP:</strong> ${device.latest_scan.ip_address}</span>` : ''}
                    <span><strong>Last Seen:</strong> ${this.formatTime(device.last_seen)}</span>
                </div>
                <div class="device-actions">
                    <button class="btn btn-secondary btn-trust" data-id="${device.id}">
                        ${device.is_trusted ? 'Untrust' : 'Trust'}
                    </button>
                    <button class="btn btn-primary btn-analyze" data-id="${device.id}">
                        Analyze
                    </button>
                </div>
            </div>
        `;
    }

    async toggleTrust(deviceId) {
        try {
            const device = this.devices.find(d => d.id == deviceId);
            if (!device) return;

            await api.updateDevice(deviceId, { is_trusted: !device.is_trusted });
            await this.loadDevices();

            window.app.showToast(
                device.is_trusted ? 'Device removed from trusted list' : 'Device added to trusted list',
                'success'
            );
        } catch (error) {
            console.error('Failed to update device:', error);
            window.app.showToast('Failed to update device', 'error');
        }
    }

    async analyzeDevice(deviceId) {
        try {
            window.app.showToast('Analyzing device...', 'info');
            const result = await api.analyzeDevice(deviceId);

            if (result.is_anomaly) {
                window.app.showToast(
                    `Anomaly detected! Score: ${(result.final_score * 100).toFixed(1)}%`,
                    'warning'
                );
            } else {
                window.app.showToast(
                    `Device appears normal. Score: ${(result.final_score * 100).toFixed(1)}%`,
                    'success'
                );
            }
        } catch (error) {
            console.error('Analysis failed:', error);
            window.app.showToast(error.message || 'Analysis failed', 'error');
        }
    }

    showDeviceDetails(deviceId) {
        console.log('Show details for device:', deviceId);
    }

    updateDeviceCount(count) {
        document.getElementById('deviceCount').textContent = count;
    }

    setFilter(key, value) {
        if (value === '' || value === undefined) {
            delete this.filters[key];
        } else {
            this.filters[key] = value;
        }
        this.currentPage = 1;
        this.loadDevices();
    }

    search(query) {
        this.setFilter('search', query);
    }

    formatTime(isoString) {
        if (!isoString) return 'Never';
        const date = new Date(isoString);
        const now = new Date();
        const diff = now - date;

        if (diff < 60000) return 'Just now';
        if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
        if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;

        return date.toLocaleDateString();
    }
}

const devicesManager = new DevicesManager();
