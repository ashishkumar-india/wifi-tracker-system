"""
Alert schemas for request/response validation.
"""

from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field


class AlertBase(BaseModel):
    """Base alert schema."""
    alert_type: str
    severity: str = "medium"
    message: str


class AlertCreate(AlertBase):
    """Schema for creating an alert."""
    device_id: Optional[int] = None
    details: Optional[dict] = None


class AlertAcknowledge(BaseModel):
    """Schema for acknowledging an alert."""
    notes: Optional[str] = None


class DeviceInfo(BaseModel):
    """Embedded device info for alerts."""
    mac_address: str
    hostname: Optional[str]
    vendor: Optional[str]


class AlertResponse(BaseModel):
    """Schema for alert response."""
    id: int
    device_id: Optional[int]
    alert_type: str
    severity: str
    message: str
    details: Optional[dict]
    is_acknowledged: bool
    acknowledged_by: Optional[int]
    acknowledged_by_username: Optional[str] = None
    created_at: datetime
    acknowledged_at: Optional[datetime]
    device: Optional[DeviceInfo] = None
    
    class Config:
        from_attributes = True


class AlertListResponse(BaseModel):
    """Schema for paginated alert list."""
    total: int
    page: int
    page_size: int
    unacknowledged_count: int
    alerts: List[AlertResponse]


class AlertStats(BaseModel):
    """Schema for alert statistics."""
    total_alerts: int
    unacknowledged: int
    by_severity: dict
    by_type: dict
    alerts_today: int
    alerts_this_week: int


class AlertFilter(BaseModel):
    """Schema for alert filtering options."""
    alert_type: Optional[str] = None
    severity: Optional[str] = None
    is_acknowledged: Optional[bool] = None
    device_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
