-- WiFi Tracker System Database Setup
-- Run this script in MySQL/XAMPP phpMyAdmin

-- Create database
CREATE DATABASE IF NOT EXISTS wifi_tracker;
USE wifi_tracker;

-- Users table for authentication
CREATE TABLE IF NOT EXISTS users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin', 'viewer') DEFAULT 'viewer',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL,
    INDEX idx_username (username),
    INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Devices table for tracked network devices
CREATE TABLE IF NOT EXISTS devices (
    id INT PRIMARY KEY AUTO_INCREMENT,
    mac_address VARCHAR(17) UNIQUE NOT NULL,
    hostname VARCHAR(255),
    vendor VARCHAR(100),
    device_type VARCHAR(50),
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_trusted BOOLEAN DEFAULT FALSE,
    is_suspicious BOOLEAN DEFAULT FALSE,
    notes TEXT,
    INDEX idx_mac_address (mac_address),
    INDEX idx_last_seen (last_seen),
    INDEX idx_is_trusted (is_trusted)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Scan results table for individual scan data points
CREATE TABLE IF NOT EXISTS scan_results (
    id INT PRIMARY KEY AUTO_INCREMENT,
    device_id INT NOT NULL,
    ip_address VARCHAR(45) NOT NULL,
    rssi INT DEFAULT NULL,
    scan_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_connected BOOLEAN DEFAULT TRUE,
    response_time_ms FLOAT DEFAULT NULL,
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE,
    INDEX idx_device_id (device_id),
    INDEX idx_scan_timestamp (scan_timestamp),
    INDEX idx_ip_address (ip_address)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Device activity log for connection/disconnection events
CREATE TABLE IF NOT EXISTS device_activity (
    id INT PRIMARY KEY AUTO_INCREMENT,
    device_id INT NOT NULL,
    event_type ENUM('connected', 'disconnected', 'ip_changed', 'hostname_changed') NOT NULL,
    old_value VARCHAR(100),
    new_value VARCHAR(100),
    event_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE,
    INDEX idx_device_activity (device_id),
    INDEX idx_event_timestamp (event_timestamp),
    INDEX idx_event_type (event_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Alerts table for security notifications
CREATE TABLE IF NOT EXISTS alerts (
    id INT PRIMARY KEY AUTO_INCREMENT,
    device_id INT,
    alert_type ENUM('new_device', 'suspicious_activity', 'anomaly_detected', 'device_offline', 'unauthorized_access') NOT NULL,
    severity ENUM('low', 'medium', 'high', 'critical') DEFAULT 'medium',
    message TEXT NOT NULL,
    details JSON,
    is_acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    acknowledged_at TIMESTAMP NULL,
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE SET NULL,
    FOREIGN KEY (acknowledged_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_alert_created (created_at),
    INDEX idx_alert_type (alert_type),
    INDEX idx_severity (severity),
    INDEX idx_acknowledged (is_acknowledged)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ML predictions table for anomaly detection results
CREATE TABLE IF NOT EXISTS ml_predictions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    device_id INT NOT NULL,
    model_type ENUM('isolation_forest', 'autoencoder', 'ensemble') NOT NULL,
    anomaly_score FLOAT NOT NULL,
    is_anomaly BOOLEAN NOT NULL,
    confidence FLOAT DEFAULT NULL,
    features JSON,
    prediction_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE,
    INDEX idx_prediction_device (device_id),
    INDEX idx_prediction_timestamp (prediction_timestamp),
    INDEX idx_is_anomaly (is_anomaly)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Scan sessions table to track scan batches
CREATE TABLE IF NOT EXISTS scan_sessions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    total_devices_found INT DEFAULT 0,
    new_devices_found INT DEFAULT 0,
    scan_type ENUM('arp', 'icmp', 'full') DEFAULT 'arp',
    network_range VARCHAR(50),
    status ENUM('running', 'completed', 'failed') DEFAULT 'running',
    error_message TEXT,
    INDEX idx_session_started (started_at),
    INDEX idx_session_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Settings table for application configuration
CREATE TABLE IF NOT EXISTS settings (
    id INT PRIMARY KEY AUTO_INCREMENT,
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value TEXT,
    setting_type ENUM('string', 'int', 'float', 'bool', 'json') DEFAULT 'string',
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_setting_key (setting_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert default settings
INSERT INTO settings (setting_key, setting_value, setting_type, description) VALUES
('scan_interval_seconds', '300', 'int', 'Interval between automatic network scans'),
('alert_new_devices', 'true', 'bool', 'Alert when new devices are detected'),
('alert_suspicious_activity', 'true', 'bool', 'Alert for suspicious device behavior'),
('ml_anomaly_threshold', '0.7', 'float', 'Threshold for ML anomaly detection'),
('network_range', '192.168.1.0/24', 'string', 'Default network range to scan'),
('email_notifications', 'false', 'bool', 'Enable email notifications'),
('webhook_url', '', 'string', 'Webhook URL for external notifications')
ON DUPLICATE KEY UPDATE setting_key = setting_key;

-- Insert default admin user (password: admin123 - CHANGE IN PRODUCTION!)
-- Password hash for 'admin123' using bcrypt
INSERT INTO users (username, email, password_hash, role) VALUES
('admin', 'admin@wifitracker.local', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.G8VrR5EGaLsIHy', 'admin')
ON DUPLICATE KEY UPDATE username = username;

-- Create views for common queries

-- View: Active devices (seen in last hour)
CREATE OR REPLACE VIEW active_devices AS
SELECT 
    d.*,
    sr.ip_address AS current_ip,
    sr.rssi AS current_rssi
FROM devices d
LEFT JOIN scan_results sr ON d.id = sr.device_id
WHERE sr.id = (
    SELECT MAX(sr2.id) 
    FROM scan_results sr2 
    WHERE sr2.device_id = d.id
)
AND d.last_seen >= DATE_SUB(NOW(), INTERVAL 1 HOUR);

-- View: Recent alerts
CREATE OR REPLACE VIEW recent_alerts AS
SELECT 
    a.*,
    d.mac_address,
    d.hostname,
    u.username AS acknowledged_by_user
FROM alerts a
LEFT JOIN devices d ON a.device_id = d.id
LEFT JOIN users u ON a.acknowledged_by = u.id
WHERE a.created_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
ORDER BY a.created_at DESC;

-- View: Device statistics
CREATE OR REPLACE VIEW device_stats AS
SELECT 
    d.id,
    d.mac_address,
    d.hostname,
    d.vendor,
    COUNT(DISTINCT sr.id) AS total_scans,
    COUNT(DISTINCT da.id) AS total_events,
    AVG(sr.rssi) AS avg_rssi,
    MIN(sr.scan_timestamp) AS first_scan,
    MAX(sr.scan_timestamp) AS last_scan
FROM devices d
LEFT JOIN scan_results sr ON d.id = sr.device_id
LEFT JOIN device_activity da ON d.id = da.device_id
GROUP BY d.id, d.mac_address, d.hostname, d.vendor;

-- Stored procedure: Clean old scan results (keep last 30 days)
DELIMITER //
CREATE PROCEDURE IF NOT EXISTS cleanup_old_data()
BEGIN
    DELETE FROM scan_results WHERE scan_timestamp < DATE_SUB(NOW(), INTERVAL 30 DAY);
    DELETE FROM device_activity WHERE event_timestamp < DATE_SUB(NOW(), INTERVAL 90 DAY);
    DELETE FROM ml_predictions WHERE prediction_timestamp < DATE_SUB(NOW(), INTERVAL 30 DAY);
    DELETE FROM alerts WHERE created_at < DATE_SUB(NOW(), INTERVAL 90 DAY) AND is_acknowledged = TRUE;
END //
DELIMITER ;

-- Event: Schedule cleanup (run weekly)
-- Note: MySQL Event Scheduler must be enabled
SET GLOBAL event_scheduler = ON;

CREATE EVENT IF NOT EXISTS weekly_cleanup
ON SCHEDULE EVERY 1 WEEK
STARTS CURRENT_TIMESTAMP
DO CALL cleanup_old_data();

SELECT 'Database setup completed successfully!' AS Status;
