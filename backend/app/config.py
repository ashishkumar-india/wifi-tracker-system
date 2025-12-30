"""
Configuration settings for the WiFi Tracker System.
Uses environment variables with sensible defaults.
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings:
    """Application settings loaded from environment variables."""
    
    # Application
    APP_NAME: str = "WiFi Tracker System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # Server
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # Database (MySQL/XAMPP)
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "3306"))
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_NAME: str = os.getenv("DB_NAME", "wifi_tracker")
    
    @property
    def DATABASE_URL(self) -> str:
        """Construct MySQL database URL."""
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    # Redis (optional caching)
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_ENABLED: bool = os.getenv("REDIS_ENABLED", "False").lower() == "true"
    
    # JWT Authentication
    SECRET_KEY: str = os.getenv("SECRET_KEY", "wifi-tracker-super-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    
    # Network Scanning
    DEFAULT_NETWORK_RANGE: str = os.getenv("NETWORK_RANGE", "192.168.1.0/24")
    SCAN_TIMEOUT: int = int(os.getenv("SCAN_TIMEOUT", "3"))
    SCAN_INTERVAL_SECONDS: int = int(os.getenv("SCAN_INTERVAL", "300"))
    MAX_CONCURRENT_SCANS: int = int(os.getenv("MAX_CONCURRENT_SCANS", "50"))
    
    # Machine Learning
    ML_MODEL_PATH: Path = BASE_DIR / "data" / "models"
    ANOMALY_THRESHOLD: float = float(os.getenv("ANOMALY_THRESHOLD", "0.7"))
    MIN_TRAINING_SAMPLES: int = int(os.getenv("MIN_TRAINING_SAMPLES", "100"))
    
    # Alerting
    ALERT_NEW_DEVICES: bool = os.getenv("ALERT_NEW_DEVICES", "True").lower() == "true"
    ALERT_SUSPICIOUS: bool = os.getenv("ALERT_SUSPICIOUS", "True").lower() == "true"
    EMAIL_ENABLED: bool = os.getenv("EMAIL_ENABLED", "False").lower() == "true"
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    ALERT_EMAIL: str = os.getenv("ALERT_EMAIL", "")
    WEBHOOK_URL: Optional[str] = os.getenv("WEBHOOK_URL", None)
    
    # CORS
    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000,http://localhost:8080").split(",")
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: Path = BASE_DIR / "logs" / "wifi_tracker.log"
    
    # OUI Database for MAC vendor lookup
    OUI_DATABASE_PATH: Path = BASE_DIR / "data" / "oui.txt"
    OUI_UPDATE_URL: str = "https://standards-oui.ieee.org/oui/oui.txt"


# Global settings instance
settings = Settings()


# Ensure required directories exist
def init_directories():
    """Create required directories if they don't exist."""
    directories = [
        settings.ML_MODEL_PATH,
        settings.LOG_FILE.parent,
        BASE_DIR / "data",
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


init_directories()
