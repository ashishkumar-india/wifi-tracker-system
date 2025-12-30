"""
API Routers package.
"""

from app.routers.auth import router as auth_router
from app.routers.devices import router as devices_router
from app.routers.scans import router as scans_router
from app.routers.alerts import router as alerts_router
from app.routers.dashboard import router as dashboard_router

__all__ = [
    "auth_router",
    "devices_router",
    "scans_router",
    "alerts_router",
    "dashboard_router"
]
