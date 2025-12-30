"""
Device activity model for tracking connection/disconnection events.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class EventType(str, enum.Enum):
    """Type of device activity event."""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    IP_CHANGED = "ip_changed"
    HOSTNAME_CHANGED = "hostname_changed"


class DeviceActivity(Base):
    """Model for device activity events."""
    
    __tablename__ = "device_activity"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    old_value = Column(String(100), nullable=True)
    new_value = Column(String(100), nullable=True)
    event_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    device = relationship("Device", back_populates="activities")
    
    def __repr__(self):
        return f"<DeviceActivity(id={self.id}, device_id={self.device_id}, type='{self.event_type}')>"
    
    def to_dict(self):
        """Convert activity to dictionary."""
        return {
            "id": self.id,
            "device_id": self.device_id,
            "event_type": self.event_type,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "event_timestamp": self.event_timestamp.isoformat() if self.event_timestamp else None
        }
    
    @classmethod
    def log_connection(cls, device_id: int, ip_address: str):
        """Create a connection event."""
        return cls(
            device_id=device_id,
            event_type="connected",
            new_value=ip_address
        )
    
    @classmethod
    def log_disconnection(cls, device_id: int, last_ip: str = None):
        """Create a disconnection event."""
        return cls(
            device_id=device_id,
            event_type="disconnected",
            old_value=last_ip
        )
    
    @classmethod
    def log_ip_change(cls, device_id: int, old_ip: str, new_ip: str):
        """Create an IP change event."""
        return cls(
            device_id=device_id,
            event_type="ip_changed",
            old_value=old_ip,
            new_value=new_ip
        )
    
    @classmethod
    def log_hostname_change(cls, device_id: int, old_hostname: str, new_hostname: str):
        """Create a hostname change event."""
        return cls(
            device_id=device_id,
            event_type="hostname_changed",
            old_value=old_hostname,
            new_value=new_hostname
        )
