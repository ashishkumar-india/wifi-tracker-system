# WiFi Tracker API Documentation

## Base URL
```
http://localhost:8000/api
```

## Authentication

All endpoints except `/auth/login` and `/auth/register` require JWT authentication.

Include the token in the Authorization header:
```
Authorization: Bearer <access_token>
```

---

## Auth Endpoints

### POST /auth/register
Register a new user account.

**Request:**
```json
{
  "username": "newuser",
  "email": "user@example.com",
  "password": "SecurePass123",
  "confirm_password": "SecurePass123"
}
```

**Response:** `201 Created`
```json
{
  "id": 2,
  "username": "newuser",
  "email": "user@example.com",
  "role": "viewer",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00",
  "last_login": null
}
```

### POST /auth/login
Authenticate and receive JWT tokens.

**Request:** (form-urlencoded)
```
username=admin&password=admin123
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### POST /auth/refresh
Refresh access token using refresh token.

**Query Parameter:**
```
refresh_token=<refresh_token>
```

### GET /auth/me
Get current user profile.

**Response:** `200 OK`
```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@wifitracker.local",
  "role": "admin",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00",
  "last_login": "2024-01-15T08:00:00"
}
```

---

## Device Endpoints

### GET /devices
List all devices with pagination and filtering.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| page | int | Page number (default: 1) |
| page_size | int | Items per page (default: 20, max: 100) |
| search | string | Search by MAC, hostname, or vendor |
| is_trusted | bool | Filter trusted devices |
| is_suspicious | bool | Filter suspicious devices |
| is_online | bool | Filter online devices |

**Response:** `200 OK`
```json
{
  "total": 45,
  "page": 1,
  "page_size": 20,
  "devices": [
    {
      "id": 1,
      "mac_address": "AA:BB:CC:DD:EE:FF",
      "hostname": "Johns-iPhone",
      "vendor": "Apple",
      "device_type": "Mobile",
      "first_seen": "2024-01-10T12:00:00",
      "last_seen": "2024-01-15T10:30:00",
      "is_trusted": true,
      "is_suspicious": false,
      "notes": null,
      "is_online": true,
      "latest_scan": {
        "id": 156,
        "ip_address": "192.168.1.105",
        "rssi": -55,
        "scan_timestamp": "2024-01-15T10:30:00",
        "is_connected": true,
        "response_time_ms": 2.5
      }
    }
  ]
}
```

### GET /devices/{id}
Get single device details.

### PUT /devices/{id}
Update device properties.

**Request:**
```json
{
  "hostname": "Custom Name",
  "is_trusted": true,
  "is_suspicious": false,
  "notes": "Corporate laptop"
}
```

### DELETE /devices/{id}
Delete a device and all related data.

### GET /devices/{id}/history
Get device activity history.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| days | int | Number of days (default: 7, max: 90) |

### POST /devices/{id}/analyze
Run ML anomaly detection on device.

**Response:** `200 OK`
```json
{
  "device_id": 1,
  "mac_address": "AA:BB:CC:DD:EE:FF",
  "predictions": {
    "isolation_forest": {
      "is_anomaly": false,
      "anomaly_score": 0.32,
      "threshold": 0.7,
      "model_type": "isolation_forest",
      "confidence": 0.68
    },
    "autoencoder": {
      "is_anomaly": false,
      "anomaly_score": 0.28,
      "reconstruction_error": 0.045,
      "threshold": 0.08,
      "model_type": "autoencoder",
      "confidence": 0.72
    }
  },
  "ensemble_decision": "consensus",
  "final_score": 0.30,
  "is_anomaly": false,
  "timestamp": "2024-01-15T10:35:00"
}
```

---

## Scan Endpoints

### POST /scans/start
Start a new network scan.

**Request:**
```json
{
  "network_range": "192.168.1.0/24",
  "scan_type": "arp",
  "timeout": 3
}
```

**Scan Types:**
- `arp` - ARP scan (fast, local network only)
- `icmp` - ICMP ping scan
- `full` - Combined ARP + ICMP

**Response:** `200 OK`
```json
{
  "id": 42,
  "started_at": "2024-01-15T10:40:00",
  "completed_at": null,
  "total_devices_found": 0,
  "new_devices_found": 0,
  "scan_type": "arp",
  "network_range": "192.168.1.0/24",
  "status": "running",
  "error_message": null,
  "duration_seconds": 0.0
}
```

### GET /scans/status
Get current scan status.

### GET /scans/history
Get scan session history.

### GET /scans/results/{session_id}
Get results for a specific scan session.

---

## Alert Endpoints

### GET /alerts
List alerts with filtering.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| page | int | Page number |
| page_size | int | Items per page |
| alert_type | string | Filter by type |
| severity | string | Filter by severity |
| is_acknowledged | bool | Filter by status |
| device_id | int | Filter by device |

**Alert Types:**
- `new_device`
- `suspicious_activity`
- `anomaly_detected`
- `device_offline`

**Severity Levels:**
- `low`
- `medium`
- `high`
- `critical`

### GET /alerts/stats
Get alert statistics.

**Response:**
```json
{
  "total_alerts": 127,
  "unacknowledged": 15,
  "by_severity": {
    "low": 45,
    "medium": 52,
    "high": 25,
    "critical": 5
  },
  "by_type": {
    "new_device": 80,
    "anomaly_detected": 30,
    "suspicious_activity": 12,
    "device_offline": 5
  },
  "alerts_today": 8,
  "alerts_this_week": 42
}
```

### PUT /alerts/{id}/acknowledge
Acknowledge an alert.

### POST /alerts/acknowledge-all
Acknowledge all unacknowledged alerts.

### DELETE /alerts/{id}
Delete an alert.

---

## Dashboard Endpoints

### GET /dashboard/stats
Get dashboard statistics.

**Response:**
```json
{
  "devices": {
    "total": 45,
    "online": 32,
    "offline": 13,
    "trusted": 28,
    "suspicious": 2,
    "new_today": 3
  },
  "alerts": {
    "total": 127,
    "unacknowledged": 15
  },
  "scans": {
    "total": 1024,
    "last_scan_time": "2024-01-15T10:30:00"
  },
  "devices_by_vendor": {
    "Apple": 15,
    "Samsung": 8,
    "Intel": 5,
    "Unknown": 17
  },
  "ml_status": {
    "isolation_forest": {"available": true, "trained": true},
    "autoencoder": {"available": true, "trained": true},
    "ensemble_enabled": true,
    "anomaly_threshold": 0.7
  }
}
```

### GET /dashboard/activity
Get activity timeline.

### GET /dashboard/device-history
Get device count history for charts.

### POST /dashboard/ml/train
Train ML models (admin only).

### GET /dashboard/ml/status
Get ML model status.

### GET /dashboard/network-info
Get local network information.

### GET /dashboard/signal-info
Get WiFi signal information.

---

## WebSocket

### WS /ws/live
Real-time updates websocket.

**Message Types:**

**Alert:**
```json
{
  "type": "alert",
  "data": {
    "id": 128,
    "alert_type": "new_device",
    "severity": "medium",
    "message": "New device detected: AA:BB:CC:DD:EE:FF"
  },
  "timestamp": "2024-01-15T10:45:00"
}
```

**Device Update:**
```json
{
  "type": "device_update",
  "event": "discovered",
  "data": {
    "mac_address": "AA:BB:CC:DD:EE:FF",
    "is_new": true
  },
  "timestamp": "2024-01-15T10:45:00"
}
```

**Scan Update:**
```json
{
  "type": "scan_update",
  "data": {
    "status": "completed",
    "session_id": 42,
    "total_devices": 35,
    "new_devices": 2
  },
  "timestamp": "2024-01-15T10:45:30"
}
```

---

## Error Responses

**400 Bad Request:**
```json
{
  "detail": "Invalid request data"
}
```

**401 Unauthorized:**
```json
{
  "detail": "Could not validate credentials"
}
```

**403 Forbidden:**
```json
{
  "detail": "Admin privileges required"
}
```

**404 Not Found:**
```json
{
  "detail": "Device not found"
}
```

**409 Conflict:**
```json
{
  "detail": "A scan is already in progress"
}
```

**500 Internal Server Error:**
```json
{
  "detail": "Internal server error"
}
```
