"""
Devices router - Device management endpoints.
"""

from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.database import get_db
from app.models.device import Device
from app.models.scan_result import ScanResult
from app.models.device_activity import DeviceActivity
from app.models.user import User
from app.schemas.device import (
    DeviceResponse, DeviceUpdate, DeviceListResponse,
    DeviceHistoryResponse, DeviceActivityResponse, ScanResultInfo
)
from app.routers.auth import get_current_user
from app.ml.detector import anomaly_detector
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/devices", tags=["Devices"])


@router.get("", response_model=DeviceListResponse)
async def list_devices(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_trusted: Optional[bool] = None,
    is_suspicious: Optional[bool] = None,
    is_online: Optional[bool] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all devices with filtering and pagination."""
    query = db.query(Device)
    
    if is_trusted is not None:
        query = query.filter(Device.is_trusted == is_trusted)
    
    if is_suspicious is not None:
        query = query.filter(Device.is_suspicious == is_suspicious)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Device.mac_address.ilike(search_pattern)) |
            (Device.hostname.ilike(search_pattern)) |
            (Device.vendor.ilike(search_pattern))
        )
    
    total = query.count()
    
    query = query.order_by(Device.last_seen.desc())
    
    offset = (page - 1) * page_size
    devices = query.offset(offset).limit(page_size).all()
    
    online_threshold = datetime.utcnow() - timedelta(minutes=10)
    
    device_responses = []
    for device in devices:
        device_online = device.last_seen >= online_threshold if device.last_seen else False
        
        if is_online is not None and device_online != is_online:
            continue
        
        latest_scan = db.query(ScanResult).filter(
            ScanResult.device_id == device.id
        ).order_by(ScanResult.scan_timestamp.desc()).first()
        
        device_responses.append(DeviceResponse(
            id=device.id,
            mac_address=device.mac_address,
            hostname=device.hostname,
            vendor=device.vendor,
            device_type=device.device_type,
            first_seen=device.first_seen,
            last_seen=device.last_seen,
            is_trusted=device.is_trusted,
            is_suspicious=device.is_suspicious,
            notes=device.notes,
            is_online=device_online,
            latest_scan=ScanResultInfo(
                id=latest_scan.id,
                ip_address=latest_scan.ip_address,
                rssi=latest_scan.rssi,
                scan_timestamp=latest_scan.scan_timestamp,
                is_connected=latest_scan.is_connected,
                response_time_ms=latest_scan.response_time_ms
            ) if latest_scan else None
        ))
    
    return DeviceListResponse(
        total=total,
        page=page,
        page_size=page_size,
        devices=device_responses
    )


@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get device details by ID."""
    device = db.query(Device).filter(Device.id == device_id).first()
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    online_threshold = datetime.utcnow() - timedelta(minutes=10)
    device_online = device.last_seen >= online_threshold if device.last_seen else False
    
    latest_scan = db.query(ScanResult).filter(
        ScanResult.device_id == device.id
    ).order_by(ScanResult.scan_timestamp.desc()).first()
    
    return DeviceResponse(
        id=device.id,
        mac_address=device.mac_address,
        hostname=device.hostname,
        vendor=device.vendor,
        device_type=device.device_type,
        first_seen=device.first_seen,
        last_seen=device.last_seen,
        is_trusted=device.is_trusted,
        is_suspicious=device.is_suspicious,
        notes=device.notes,
        is_online=device_online,
        latest_scan=ScanResultInfo(
            id=latest_scan.id,
            ip_address=latest_scan.ip_address,
            rssi=latest_scan.rssi,
            scan_timestamp=latest_scan.scan_timestamp,
            is_connected=latest_scan.is_connected,
            response_time_ms=latest_scan.response_time_ms
        ) if latest_scan else None
    )


@router.put("/{device_id}", response_model=DeviceResponse)
async def update_device(
    device_id: int,
    update_data: DeviceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update device properties."""
    device = db.query(Device).filter(Device.id == device_id).first()
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    if update_data.hostname is not None:
        device.hostname = update_data.hostname
    if update_data.device_type is not None:
        device.device_type = update_data.device_type
    if update_data.is_trusted is not None:
        device.is_trusted = update_data.is_trusted
    if update_data.is_suspicious is not None:
        device.is_suspicious = update_data.is_suspicious
    if update_data.notes is not None:
        device.notes = update_data.notes
    
    db.commit()
    db.refresh(device)
    
    logger.info(f"Device {device.mac_address} updated by {current_user.username}")
    
    online_threshold = datetime.utcnow() - timedelta(minutes=10)
    device_online = device.last_seen >= online_threshold if device.last_seen else False
    
    return DeviceResponse(
        id=device.id,
        mac_address=device.mac_address,
        hostname=device.hostname,
        vendor=device.vendor,
        device_type=device.device_type,
        first_seen=device.first_seen,
        last_seen=device.last_seen,
        is_trusted=device.is_trusted,
        is_suspicious=device.is_suspicious,
        notes=device.notes,
        is_online=device_online,
        latest_scan=None
    )


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_device(
    device_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a device."""
    device = db.query(Device).filter(Device.id == device_id).first()
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    mac = device.mac_address
    db.delete(device)
    db.commit()
    
    logger.info(f"Device {mac} deleted by {current_user.username}")


@router.get("/{device_id}/history", response_model=DeviceHistoryResponse)
async def get_device_history(
    device_id: int,
    days: int = Query(7, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get device activity history."""
    device = db.query(Device).filter(Device.id == device_id).first()
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    activities = db.query(DeviceActivity).filter(
        DeviceActivity.device_id == device_id,
        DeviceActivity.event_timestamp >= cutoff
    ).order_by(DeviceActivity.event_timestamp.desc()).limit(100).all()
    
    scans = db.query(ScanResult).filter(
        ScanResult.device_id == device_id,
        ScanResult.scan_timestamp >= cutoff
    ).order_by(ScanResult.scan_timestamp.desc()).limit(100).all()
    
    online_threshold = datetime.utcnow() - timedelta(minutes=10)
    device_online = device.last_seen >= online_threshold if device.last_seen else False
    
    return DeviceHistoryResponse(
        device=DeviceResponse(
            id=device.id,
            mac_address=device.mac_address,
            hostname=device.hostname,
            vendor=device.vendor,
            device_type=device.device_type,
            first_seen=device.first_seen,
            last_seen=device.last_seen,
            is_trusted=device.is_trusted,
            is_suspicious=device.is_suspicious,
            notes=device.notes,
            is_online=device_online,
            latest_scan=None
        ),
        activities=[
            DeviceActivityResponse(
                id=a.id,
                device_id=a.device_id,
                event_type=a.event_type,
                old_value=a.old_value,
                new_value=a.new_value,
                event_timestamp=a.event_timestamp
            ) for a in activities
        ],
        scan_results=[
            ScanResultInfo(
                id=s.id,
                ip_address=s.ip_address,
                rssi=s.rssi,
                scan_timestamp=s.scan_timestamp,
                is_connected=s.is_connected,
                response_time_ms=s.response_time_ms
            ) for s in scans
        ]
    )


@router.post("/{device_id}/analyze")
async def analyze_device(
    device_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Run ML anomaly detection on a device."""
    device = db.query(Device).filter(Device.id == device_id).first()
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    if not anomaly_detector.is_trained():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ML models not trained. Train models first."
        )
    
    scan_results = db.query(ScanResult).filter(
        ScanResult.device_id == device_id
    ).all()
    
    activities = db.query(DeviceActivity).filter(
        DeviceActivity.device_id == device_id
    ).all()
    
    device_info = device.to_dict()
    
    prediction = anomaly_detector.predict(
        [s.to_dict() for s in scan_results],
        [a.to_dict() for a in activities],
        device_info
    )
    
    return prediction
