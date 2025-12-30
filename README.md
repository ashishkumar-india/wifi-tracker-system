# WiFi Tracker System

<div align="center">

![WiFi Tracker](https://img.shields.io/badge/WiFi-Tracker-6366f1?style=for-the-badge&logo=wifi&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-XAMPP-4479A1?style=for-the-badge&logo=mysql&logoColor=white)

**An AI-powered WiFi device tracking and network security monitoring system**

</div>

---

## Overview

WiFi Tracker is a production-ready network security monitoring system designed for cybersecurity research and enterprise network management. It provides real-time device discovery, behavioral analysis, and machine learning-based anomaly detection.

### Key Features

- **Network Scanning**: ARP and ICMP-based device discovery
- **Device Fingerprinting**: MAC vendor identification and device classification
- **Signal Analysis**: RSSI monitoring and connection quality metrics
- **ML Anomaly Detection**: Isolation Forest and Autoencoder models
- **Real-time Monitoring**: WebSocket-based live updates
- **Alert System**: Configurable notifications via WebSocket, email, and webhooks
- **Modern Dashboard**: Responsive dark-themed web interface
- **JWT Authentication**: Secure role-based access control

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  HTML/CSS/JavaScript Dashboard with Chart.js             │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────┬───────────────────────────────────────┘
                          │ HTTP/WebSocket
┌─────────────────────────▼───────────────────────────────────────┐
│                      FastAPI Backend                             │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌──────────┐  │
│  │   Auth     │  │  Devices   │  │   Scans    │  │  Alerts  │  │
│  └────────────┘  └────────────┘  └────────────┘  └──────────┘  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              Services Layer                                 │ │
│  │  Scanner │ Fingerprinter │ Signal Analyzer │ Notifications │ │
│  └────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              ML Module                                      │ │
│  │  Feature Extractor │ Isolation Forest │ Autoencoder        │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                    MySQL Database (XAMPP)                        │
│  users │ devices │ scan_results │ alerts │ ml_predictions       │
└─────────────────────────────────────────────────────────────────┘
```

---

## Requirements

### System Requirements
- Python 3.9 or higher
- XAMPP (MySQL 8.0+)
- Windows/Linux/macOS
- Administrator privileges (for network scanning)

### Python Dependencies
See `backend/requirements.txt` for full list.

---

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/wifi-tracker.git
cd wifi-tracker
```

### 2. Setup Database

1. Start XAMPP and ensure MySQL is running
2. Open phpMyAdmin (http://localhost/phpmyadmin)
3. Import `scripts/setup_database.sql`

Or via command line:
```bash
mysql -u root -p < scripts/setup_database.sql
```

### 3. Configure Environment

```bash
cd backend
copy .env.example .env
# Edit .env with your settings
```

Key configurations:
```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=
DB_NAME=wifi_tracker
SECRET_KEY=your-secret-key-here
NETWORK_RANGE=192.168.1.0/24
```

### 4. Install Python Dependencies

```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

### 5. Run the Application

```bash
# Run as Administrator for network scanning
python run.py
```

The API will be available at:
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **Frontend**: Open `frontend/index.html` in browser

---

## API Documentation

### Authentication

#### Login
```http
POST /api/auth/login
Content-Type: application/x-www-form-urlencoded

username=admin&password=admin123
```

Response:
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### Devices

#### List Devices
```http
GET /api/devices?page=1&page_size=20
Authorization: Bearer <token>
```

#### Analyze Device
```http
POST /api/devices/{id}/analyze
Authorization: Bearer <token>
```

### Scans

#### Start Network Scan
```http
POST /api/scans/start
Authorization: Bearer <token>
Content-Type: application/json

{
  "network_range": "192.168.1.0/24",
  "scan_type": "arp",
  "timeout": 3
}
```

### Alerts

#### List Alerts
```http
GET /api/alerts?is_acknowledged=false
Authorization: Bearer <token>
```

#### Acknowledge Alert
```http
PUT /api/alerts/{id}/acknowledge
Authorization: Bearer <token>
```

### Machine Learning

#### Train Models
```http
POST /api/dashboard/ml/train
Authorization: Bearer <token>
```

---

## Database Schema

### Tables

| Table | Description |
|-------|-------------|
| `users` | User accounts for authentication |
| `devices` | Discovered network devices |
| `scan_results` | Individual scan data points |
| `device_activity` | Connection/disconnection events |
| `alerts` | Security notifications |
| `ml_predictions` | Anomaly detection results |
| `scan_sessions` | Scan batch tracking |
| `settings` | Application configuration |

---

## Machine Learning Models

### Isolation Forest
- **Type**: Unsupervised anomaly detection
- **Use Case**: Detecting outliers in device behavior
- **Features**: Connection patterns, RSSI variance, activity entropy

### Autoencoder
- **Type**: Deep learning reconstruction
- **Architecture**: Encoder-Decoder neural network
- **Use Case**: Complex pattern anomaly detection

### Features Used
1. Connection count
2. Average/std session duration
3. Unique IPs used
4. IP change frequency
5. Average RSSI
6. RSSI variance
7. Hour entropy
8. Day-of-week entropy
9. Connection regularity
10. Time since first seen
11. Average response time
12. Offline frequency
13. Trust status
14. Vendor known

---

## Security Considerations

1. **Run as Administrator**: Required for raw network access
2. **Change Default Credentials**: Update admin password immediately
3. **Secure SECRET_KEY**: Use a strong random key in production
4. **Network Authorization**: Ensure you have permission to scan
5. **HTTPS**: Use a reverse proxy with SSL in production

---

## Troubleshooting

### "No libpcap provider available" Warning
The scanner works without Npcap/WinPcap by using a fallback method (ping + ARP table).

**To enable full ARP scanning (optional):**
1. Download [Npcap](https://npcap.com/#download)
2. Run installer with **"WinPcap API-compatible Mode"** checked
3. Restart the application

### Scapy/Network Permission Error
```
Run the application as Administrator/root for full scanning capabilities
```

### Database Connection Error
```
1. Ensure XAMPP MySQL is running
2. Check DB credentials in .env
3. Verify database 'wifi_tracker' exists
```

### WebSocket Not Connecting
```
1. Verify the backend is running on port 8000
2. Check CORS settings if using different origins
3. Ensure firewall allows WebSocket connections
```

### PyTorch Model Loading Warning
If you see `WeightsUnpickler error` warnings, this is normal for PyTorch 2.6+.
The application handles this automatically with `weights_only=False`.

### "Failed to start scan" or Network Range Error
- Leave the Network Range field **empty** to use auto-detected network
- Or enter valid CIDR format: `192.168.1.0/24`
- Single IP addresses are auto-converted to /24 networks

### "Failed to load alerts" Error
Ensure the backend is running and database tables are properly initialized.
Check backend logs for specific error messages.

### "Analyze" Button Shows Error
- Verify ML models are trained (go to ML Detection → Train Models)
- Check backend logs for numpy serialization issues

---

## License

This project is licensed under the MIT License.

---

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

---

## Acknowledgments

- FastAPI for the excellent web framework
- Scapy for network packet manipulation
- PyTorch for deep learning capabilities
- Chart.js for beautiful visualizations
