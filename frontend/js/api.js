/**
 * WiFi Tracker - API Client
 * Handles all HTTP requests to the backend
 */

const API_BASE_URL = 'http://localhost:8000/api';

class ApiClient {
    constructor() {
        this.baseUrl = API_BASE_URL;
        this.token = localStorage.getItem('access_token');
    }

    setToken(token) {
        this.token = token;
        localStorage.setItem('access_token', token);
    }

    clearToken() {
        this.token = null;
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };

        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }

        try {
            const response = await fetch(url, {
                ...options,
                headers
            });

            if (response.status === 401) {
                const refreshed = await this.refreshToken();
                if (refreshed) {
                    headers['Authorization'] = `Bearer ${this.token}`;
                    const retryResponse = await fetch(url, { ...options, headers });
                    return this.handleResponse(retryResponse);
                } else {
                    this.clearToken();
                    window.location.reload();
                    throw new Error('Session expired');
                }
            }

            return this.handleResponse(response);
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    async handleResponse(response) {
        const contentType = response.headers.get('content-type');
        
        if (response.status === 204) {
            return null;
        }

        if (contentType && contentType.includes('application/json')) {
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.detail || 'Request failed');
            }
            
            return data;
        }

        if (!response.ok) {
            throw new Error('Request failed');
        }

        return await response.text();
    }

    async refreshToken() {
        const refreshToken = localStorage.getItem('refresh_token');
        if (!refreshToken) return false;

        try {
            const response = await fetch(`${this.baseUrl}/auth/refresh?refresh_token=${refreshToken}`, {
                method: 'POST'
            });

            if (response.ok) {
                const data = await response.json();
                this.setToken(data.access_token);
                localStorage.setItem('refresh_token', data.refresh_token);
                return true;
            }
        } catch (error) {
            console.error('Token refresh failed:', error);
        }

        return false;
    }

    // Auth endpoints
    async login(username, password) {
        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);

        const response = await fetch(`${this.baseUrl}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Login failed');
        }

        this.setToken(data.access_token);
        localStorage.setItem('refresh_token', data.refresh_token);
        return data;
    }

    async getCurrentUser() {
        return this.request('/auth/me');
    }

    // Dashboard endpoints
    async getDashboardStats() {
        return this.request('/dashboard/stats');
    }

    async getActivityTimeline(hours = 24) {
        return this.request(`/dashboard/activity?hours=${hours}`);
    }

    async getDeviceHistory(days = 7) {
        return this.request(`/dashboard/device-history?days=${days}`);
    }

    async getNetworkInfo() {
        return this.request('/dashboard/network-info');
    }

    async getSignalInfo() {
        return this.request('/dashboard/signal-info');
    }

    async getMlStatus() {
        return this.request('/dashboard/ml/status');
    }

    async trainModels() {
        return this.request('/dashboard/ml/train', { method: 'POST' });
    }

    // Devices endpoints
    async getDevices(page = 1, pageSize = 20, filters = {}) {
        const params = new URLSearchParams({ page, page_size: pageSize });
        
        if (filters.search) params.append('search', filters.search);
        if (filters.is_trusted !== undefined) params.append('is_trusted', filters.is_trusted);
        if (filters.is_suspicious !== undefined) params.append('is_suspicious', filters.is_suspicious);
        if (filters.is_online !== undefined) params.append('is_online', filters.is_online);

        return this.request(`/devices?${params}`);
    }

    async getDevice(id) {
        return this.request(`/devices/${id}`);
    }

    async updateDevice(id, data) {
        return this.request(`/devices/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    async deleteDevice(id) {
        return this.request(`/devices/${id}`, { method: 'DELETE' });
    }

    async getDeviceHistory(id, days = 7) {
        return this.request(`/devices/${id}/history?days=${days}`);
    }

    async analyzeDevice(id) {
        return this.request(`/devices/${id}/analyze`, { method: 'POST' });
    }

    // Scan endpoints
    async startScan(options = {}) {
        return this.request('/scans/start', {
            method: 'POST',
            body: JSON.stringify({
                network_range: options.networkRange || null,
                scan_type: options.scanType || 'arp',
                timeout: options.timeout || 3
            })
        });
    }

    async getScanStatus() {
        return this.request('/scans/status');
    }

    async getScanHistory(page = 1, pageSize = 20) {
        return this.request(`/scans/history?page=${page}&page_size=${pageSize}`);
    }

    async getScanResults(sessionId) {
        return this.request(`/scans/results/${sessionId}`);
    }

    // Alerts endpoints
    async getAlerts(page = 1, pageSize = 20, filters = {}) {
        const params = new URLSearchParams({ page, page_size: pageSize });
        
        if (filters.alert_type) params.append('alert_type', filters.alert_type);
        if (filters.severity) params.append('severity', filters.severity);
        if (filters.is_acknowledged !== undefined) params.append('is_acknowledged', filters.is_acknowledged);

        return this.request(`/alerts?${params}`);
    }

    async getAlertStats() {
        return this.request('/alerts/stats');
    }

    async acknowledgeAlert(id) {
        return this.request(`/alerts/${id}/acknowledge`, { method: 'PUT' });
    }

    async acknowledgeAllAlerts() {
        return this.request('/alerts/acknowledge-all', { method: 'POST' });
    }

    async deleteAlert(id) {
        return this.request(`/alerts/${id}`, { method: 'DELETE' });
    }
}

const api = new ApiClient();
