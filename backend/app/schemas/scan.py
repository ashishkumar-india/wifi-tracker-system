"""
Scan-related schemas.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, validator
import re


class ScanRequest(BaseModel):
    """Schema for initiating a network scan."""
    network_range: Optional[str] = None
    scan_type: str = Field(default="arp", pattern="^(arp|icmp|full)$")
    timeout: int = Field(default=3, ge=1, le=30)
    
    @validator('network_range')
    def validate_network_range(cls, v):
        """Validate CIDR network range format."""
        if v is None:
            return v
        cidr_pattern = r'^(\d{1,3}\.){3}\d{1,3}/\d{1,2}$'
        if not re.match(cidr_pattern, v):
            raise ValueError('Invalid network range format. Expected: X.X.X.X/XX')
        return v


class ScanResultResponse(BaseModel):
    """Schema for individual scan result."""
    id: int
    device_id: int
    ip_address: str
    rssi: Optional[int]
    scan_timestamp: datetime
    is_connected: bool
    response_time_ms: Optional[float]
    device_mac: Optional[str] = None
    device_hostname: Optional[str] = None
    device_vendor: Optional[str] = None
    
    class Config:
        from_attributes = True


class ScanSessionResponse(BaseModel):
    """Schema for scan session response."""
    id: int
    started_at: datetime
    completed_at: Optional[datetime]
    total_devices_found: int
    new_devices_found: int
    scan_type: str
    network_range: Optional[str]
    status: str
    error_message: Optional[str]
    duration_seconds: float
    
    class Config:
        from_attributes = True


class ScanStatusResponse(BaseModel):
    """Schema for current scan status."""
    is_scanning: bool
    current_session: Optional[ScanSessionResponse]
    last_scan_time: Optional[datetime]
    next_scheduled_scan: Optional[datetime]
    devices_found_in_current_scan: int = 0


class DiscoveredDevice(BaseModel):
    """Schema for a discovered device during scan."""
    mac_address: str
    ip_address: str
    hostname: Optional[str]
    vendor: Optional[str]
    rssi: Optional[int]
    response_time_ms: Optional[float]
    is_new: bool = False


class ScanResultsSummary(BaseModel):
    """Schema for scan results summary."""
    session: ScanSessionResponse
    discovered_devices: List[DiscoveredDevice]
    new_devices: List[DiscoveredDevice]
    offline_devices: List[str]  # MAC addresses of devices that went offline


class NetworkInfo(BaseModel):
    """Schema for network information."""
    interface: str
    ip_address: str
    netmask: str
    gateway: Optional[str]
    network_range: str
