"""
Pydantic schemas package.
"""

from app.schemas.auth import (
    Token,
    TokenData,
    UserCreate,
    UserLogin,
    UserResponse,
    UserUpdate
)
from app.schemas.device import (
    DeviceBase,
    DeviceCreate,
    DeviceUpdate,
    DeviceResponse,
    DeviceListResponse
)
from app.schemas.scan import (
    ScanRequest,
    ScanResultResponse,
    ScanSessionResponse,
    ScanStatusResponse
)
from app.schemas.alert import (
    AlertBase,
    AlertCreate,
    AlertResponse,
    AlertListResponse,
    AlertAcknowledge
)

__all__ = [
    # Auth
    "Token",
    "TokenData",
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "UserUpdate",
    # Device
    "DeviceBase",
    "DeviceCreate",
    "DeviceUpdate",
    "DeviceResponse",
    "DeviceListResponse",
    # Scan
    "ScanRequest",
    "ScanResultResponse",
    "ScanSessionResponse",
    "ScanStatusResponse",
    # Alert
    "AlertBase",
    "AlertCreate",
    "AlertResponse",
    "AlertListResponse",
    "AlertAcknowledge"
]
