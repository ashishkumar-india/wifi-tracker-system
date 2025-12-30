"""
Dashboard router - Dashboard statistics and ML training endpoints.
"""

from datetime import datetime, timedelta
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.device import Device
from app.models.scan_result import ScanResult, ScanSession
from app.models.device_activity import DeviceActivity
from app.models.alert import Alert
from app.models.user import User
from app.routers.auth import get_current_user, get_current_admin
from app.ml.detector import anomaly_detector
from app.schemas.device import DeviceStatsResponse
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats")
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get dashboard statistics."""
    total_devices = db.query(Device).count()
    
    online_threshold = datetime.utcnow() - timedelta(minutes=10)
    online_devices = db.query(Device).filter(
        Device.last_seen >= online_threshold
    ).count()
    
    trusted_devices = db.query(Device).filter(Device.is_trusted == True).count()
    suspicious_devices = db.query(Device).filter(Device.is_suspicious == True).count()
    
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    new_devices_today = db.query(Device).filter(Device.first_seen >= today).count()
    
    total_alerts = db.query(Alert).count()
    unacknowledged_alerts = db.query(Alert).filter(Alert.is_acknowledged == False).count()
    
    total_scans = db.query(ScanSession).filter(
        ScanSession.status == "completed"
    ).count()
    
    last_scan = db.query(ScanSession).filter(
        ScanSession.status == "completed"
    ).order_by(ScanSession.completed_at.desc()).first()
    
    vendor_counts = db.query(
        Device.vendor, func.count(Device.id)
    ).filter(Device.vendor.isnot(None)).group_by(Device.vendor).all()
    
    devices_by_vendor = {vendor: count for vendor, count in vendor_counts if vendor}
    
    return {
        "devices": {
            "total": total_devices,
            "online": online_devices,
            "offline": total_devices - online_devices,
            "trusted": trusted_devices,
            "suspicious": suspicious_devices,
            "new_today": new_devices_today
        },
        "alerts": {
            "total": total_alerts,
            "unacknowledged": unacknowledged_alerts
        },
        "scans": {
            "total": total_scans,
            "last_scan_time": last_scan.completed_at.isoformat() if last_scan else None
        },
        "devices_by_vendor": devices_by_vendor,
        "ml_status": anomaly_detector.get_model_status()
    }


@router.get("/activity")
async def get_activity_timeline(
    hours: int = 24,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get device activity timeline."""
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    
    activities = db.query(DeviceActivity).filter(
        DeviceActivity.event_timestamp >= cutoff
    ).order_by(DeviceActivity.event_timestamp.desc()).limit(100).all()
    
    timeline = []
    for activity in activities:
        device = db.query(Device).filter(Device.id == activity.device_id).first()
        timeline.append({
            "id": activity.id,
            "event_type": activity.event_type,
            "timestamp": activity.event_timestamp.isoformat(),
            "device_mac": device.mac_address if device else None,
            "device_hostname": device.hostname if device else None,
            "old_value": activity.old_value,
            "new_value": activity.new_value
        })
    
    return {"timeline": timeline}


@router.get("/device-history")
async def get_device_count_history(
    days: int = 7,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get historical device count data for charts."""
    history = []
    
    for i in range(days, -1, -1):
        day = datetime.utcnow().replace(
            hour=0, minute=0, second=0, microsecond=0
        ) - timedelta(days=i)
        
        next_day = day + timedelta(days=1)
        
        count = db.query(Device).filter(
            Device.first_seen < next_day
        ).count()
        
        new_devices = db.query(Device).filter(
            Device.first_seen >= day,
            Device.first_seen < next_day
        ).count()
        
        history.append({
            "date": day.strftime("%Y-%m-%d"),
            "total_devices": count,
            "new_devices": new_devices
        })
    
    return {"history": history}


@router.post("/ml/train")
async def train_ml_models(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Train ML models on current device data."""
    devices = db.query(Device).all()
    
    devices_data = []
    for device in devices:
        scan_results = db.query(ScanResult).filter(
            ScanResult.device_id == device.id
        ).all()
        
        activities = db.query(DeviceActivity).filter(
            DeviceActivity.device_id == device.id
        ).all()
        
        devices_data.append({
            "device_info": device.to_dict(),
            "scan_results": [sr.to_dict() for sr in scan_results],
            "activities": [a.to_dict() for a in activities]
        })
    
    results = anomaly_detector.train(devices_data)
    
    logger.info(f"ML training initiated by {current_user.username}: {results}")
    
    return results


@router.get("/ml/status")
async def get_ml_status(
    current_user: User = Depends(get_current_user)
):
    """Get ML model status."""
    return anomaly_detector.get_model_status()


@router.get("/network-info")
async def get_network_info(
    current_user: User = Depends(get_current_user)
):
    """Get local network information."""
    from app.services.scanner import NetworkScanner
    
    scanner = NetworkScanner()
    info = scanner.get_local_network_info()
    
    return info


@router.get("/signal-info")
async def get_signal_info(
    current_user: User = Depends(get_current_user)
):
    """Get WiFi signal information."""
    from app.services.signal_analyzer import signal_analyzer
    
    signal = signal_analyzer.get_wifi_signal_info()
    
    if signal:
        return {
            "rssi": signal.rssi,
            "quality_percent": signal.quality_percent,
            "noise_level": signal.noise_level,
            "link_speed": signal.link_speed,
            "frequency": signal.frequency,
            "channel": signal.channel
        }
    
    return {"error": "Could not retrieve signal information"}
