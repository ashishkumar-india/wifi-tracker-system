"""
Device schemas for request/response validation.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, validator
import re


class DeviceBase(BaseModel):
    """Base device schema."""
    mac_address: str = Field(..., min_length=17, max_length=17)
    hostname: Optional[str] = None
    vendor: Optional[str] = None
    device_type: Optional[str] = None
    
    @validator('mac_address')
    def validate_mac_address(cls, v):
        """Validate MAC address format."""
        mac_pattern = r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$'
        if not re.match(mac_pattern, v):
            raise ValueError('Invalid MAC address format. Expected: XX:XX:XX:XX:XX:XX')
        return v.upper()


class DeviceCreate(DeviceBase):
    """Schema for creating a new device."""
    ip_address: Optional[str] = None
    is_trusted: bool = False
    notes: Optional[str] = None


class DeviceUpdate(BaseModel):
    """Schema for updating a device."""
    hostname: Optional[str] = None
    device_type: Optional[str] = None
    is_trusted: Optional[bool] = None
    is_suspicious: Optional[bool] = None
    notes: Optional[str] = None


class ScanResultInfo(BaseModel):
    """Embedded scan result info."""
    id: int
    ip_address: str
    rssi: Optional[int]
    scan_timestamp: datetime
    is_connected: bool
    response_time_ms: Optional[float]
    
    class Config:
        from_attributes = True


class DeviceResponse(BaseModel):
    """Schema for device response."""
    id: int
    mac_address: str
    hostname: Optional[str]
    vendor: Optional[str]
    device_type: Optional[str]
    first_seen: datetime
    last_seen: datetime
    is_trusted: bool
    is_suspicious: bool
    notes: Optional[str]
    is_online: bool = False
    latest_scan: Optional[ScanResultInfo] = None
    
    class Config:
        from_attributes = True


class DeviceListResponse(BaseModel):
    """Schema for paginated device list response."""
    total: int
    page: int
    page_size: int
    devices: List[DeviceResponse]


class DeviceActivityResponse(BaseModel):
    """Schema for device activity response."""
    id: int
    device_id: int
    event_type: str
    old_value: Optional[str]
    new_value: Optional[str]
    event_timestamp: datetime
    
    class Config:
        from_attributes = True


class DeviceHistoryResponse(BaseModel):
    """Schema for device history."""
    device: DeviceResponse
    activities: List[DeviceActivityResponse]
    scan_results: List[ScanResultInfo]


class DeviceStatsResponse(BaseModel):
    """Schema for device statistics."""
    total_devices: int
    online_devices: int
    trusted_devices: int
    suspicious_devices: int
    new_devices_today: int
    devices_by_vendor: dict
