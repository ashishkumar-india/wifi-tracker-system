/**
 * WiFi Tracker - Alerts Module
 */

class AlertsManager {
    constructor() {
        this.alerts = [];
        this.currentPage = 1;
        this.pageSize = 20;
        this.filters = {};
    }

    async loadAlerts() {
        const list = document.getElementById('alertsList');
        list.innerHTML = '<div class="loading-spinner">Loading alerts...</div>';

        try {
            const response = await api.getAlerts(this.currentPage, this.pageSize, this.filters);
            this.alerts = response.alerts;
            this.renderAlerts();
            this.updateAlertCount(response.unacknowledged_count);
        } catch (error) {
            console.error('Failed to load alerts:', error);
            list.innerHTML = '<p class="error">Failed to load alerts</p>';
        }
    }

    renderAlerts() {
        const list = document.getElementById('alertsList');

        if (this.alerts.length === 0) {
            list.innerHTML = '<p class="no-data">No alerts found</p>';
            return;
        }

        list.innerHTML = this.alerts.map(alert => this.renderAlertItem(alert)).join('');

        list.querySelectorAll('.btn-ack').forEach(btn => {
            btn.addEventListener('click', () => this.acknowledgeAlert(btn.dataset.id));
        });

        list.querySelectorAll('.btn-delete').forEach(btn => {
            btn.addEventListener('click', () => this.deleteAlert(btn.dataset.id));
        });
    }

    renderAlertItem(alert) {
        const iconClass = this.getIconClass(alert.alert_type);
        const unreadClass = alert.is_acknowledged ? '' : 'unread';
        const criticalClass = alert.severity === 'critical' ? 'critical' : '';

        return `
            <div class="alert-item ${unreadClass} ${criticalClass}" data-id="${alert.id}">
                <div class="alert-icon ${iconClass}">
                    ${this.getIcon(alert.alert_type)}
                </div>
                <div class="alert-content">
                    <div class="alert-title">
                        ${this.formatAlertType(alert.alert_type)}
                        <span class="severity-badge ${alert.severity}">${alert.severity}</span>
                    </div>
                    <div class="alert-message">${alert.message}</div>
                    <div class="alert-meta">
                        <span>${this.formatTime(alert.created_at)}</span>
                        ${alert.device ? `<span>Device: ${alert.device.mac_address}</span>` : ''}
                        ${alert.is_acknowledged ? `<span>Acknowledged by ${alert.acknowledged_by_username}</span>` : ''}
                    </div>
                </div>
                <div class="alert-actions">
                    ${!alert.is_acknowledged ? `
                        <button class="btn btn-secondary btn-ack" data-id="${alert.id}">
                            Acknowledge
                        </button>
                    ` : ''}
                    <button class="btn-icon btn-delete" data-id="${alert.id}" title="Delete">
                        <svg width="16" height="16" viewBox="0 0 20 20" fill="currentColor">
                            <path fill-rule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z"/>
                        </svg>
                    </button>
                </div>
            </div>
        `;
    }

    getIconClass(type) {
        switch (type) {
            case 'new_device': return 'new';
            case 'anomaly_detected': return 'danger';
            case 'suspicious_activity': return 'alert';
            case 'device_offline': return 'info';
            default: return 'info';
        }
    }

    getIcon(type) {
        switch (type) {
            case 'new_device':
                return '<svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-11a1 1 0 10-2 0v2H7a1 1 0 100 2h2v2a1 1 0 102 0v-2h2a1 1 0 100-2h-2V7z"/></svg>';
            case 'anomaly_detected':
                return '<svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"/></svg>';
            case 'suspicious_activity':
                return '<svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"/></svg>';
            default:
                return '<svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"/></svg>';
        }
    }

    formatAlertType(type) {
        return type.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
    }

    async acknowledgeAlert(alertId) {
        try {
            await api.acknowledgeAlert(alertId);
            await this.loadAlerts();
            window.app.showToast('Alert acknowledged', 'success');
        } catch (error) {
            console.error('Failed to acknowledge alert:', error);
            window.app.showToast('Failed to acknowledge alert', 'error');
        }
    }

    async acknowledgeAll() {
        try {
            const result = await api.acknowledgeAllAlerts();
            await this.loadAlerts();
            window.app.showToast(`${result.acknowledged_count} alerts acknowledged`, 'success');
        } catch (error) {
            console.error('Failed to acknowledge alerts:', error);
            window.app.showToast('Failed to acknowledge alerts', 'error');
        }
    }

    async deleteAlert(alertId) {
        try {
            await api.deleteAlert(alertId);
            await this.loadAlerts();
            window.app.showToast('Alert deleted', 'success');
        } catch (error) {
            console.error('Failed to delete alert:', error);
            window.app.showToast('Failed to delete alert', 'error');
        }
    }

    updateAlertCount(count) {
        const badge = document.getElementById('alertCount');
        badge.textContent = count;
        badge.style.display = count > 0 ? 'inline' : 'none';
    }

    setFilter(key, value) {
        if (value === '' || value === undefined) {
            delete this.filters[key];
        } else {
            this.filters[key] = value;
        }
        this.currentPage = 1;
        this.loadAlerts();
    }

    formatTime(isoString) {
        if (!isoString) return '';
        const date = new Date(isoString);
        const now = new Date();
        const diff = now - date;

        if (diff < 60000) return 'Just now';
        if (diff < 3600000) return `${Math.floor(diff / 60000)} minutes ago`;
        if (diff < 86400000) return `${Math.floor(diff / 3600000)} hours ago`;

        return date.toLocaleString();
    }
}

const alertsManager = new AlertsManager();
