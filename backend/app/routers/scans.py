"""
Scans router - Network scanning endpoints.
"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.device import Device
from app.models.scan_result import ScanResult, ScanSession, ScanType, ScanStatus
from app.models.device_activity import DeviceActivity, EventType
from app.models.alert import Alert
from app.models.user import User
from app.schemas.scan import (
    ScanRequest, ScanSessionResponse, ScanStatusResponse,
    ScanResultsSummary, DiscoveredDevice
)
from app.routers.auth import get_current_user, get_current_admin
from app.services.scanner import NetworkScanner
from app.services.fingerprinter import fingerprinter
from app.services.notification import notification_service
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/scans", tags=["Scans"])

_current_scan_session: Optional[ScanSession] = None


async def perform_scan(
    scan_request: ScanRequest,
    session_id: int,
    db: Session
):
    """Background task to perform network scan."""
    global _current_scan_session
    
    try:
        session = db.query(ScanSession).filter(ScanSession.id == session_id).first()
        if not session:
            return
        
        scanner = NetworkScanner(
            network_range=scan_request.network_range or settings.DEFAULT_NETWORK_RANGE,
            timeout=scan_request.timeout
        )
        
        if scan_request.scan_type == "arp":
            results = scanner.arp_scan()
        elif scan_request.scan_type == "icmp":
            results = scanner.icmp_scan()
        else:
            results = scanner.full_scan()
        
        new_devices = 0
        total_devices = len(results)
        
        for result in results:
            device = db.query(Device).filter(
                Device.mac_address == result.mac_address
            ).first()
            
            is_new = False
            
            if not device:
                fingerprint = fingerprinter.fingerprint(
                    result.mac_address,
                    result.hostname
                )
                
                device = Device(
                    mac_address=result.mac_address,
                    hostname=result.hostname,
                    vendor=fingerprint.get("vendor"),
                    device_type=fingerprint.get("device_type")
                )
                db.add(device)
                db.flush()
                
                is_new = True
                new_devices += 1
                
                if settings.ALERT_NEW_DEVICES:
                    alert = Alert.create_new_device_alert(
                        device.id,
                        device.mac_address,
                        device.vendor
                    )
                    db.add(alert)
                    
                    await notification_service.send_alert(alert.to_dict())
                
                activity = DeviceActivity.log_connection(device.id, result.ip_address)
                db.add(activity)
            else:
                last_scan = db.query(ScanResult).filter(
                    ScanResult.device_id == device.id
                ).order_by(ScanResult.scan_timestamp.desc()).first()
                
                if last_scan and last_scan.ip_address != result.ip_address:
                    activity = DeviceActivity.log_ip_change(
                        device.id, last_scan.ip_address, result.ip_address
                    )
                    db.add(activity)
                
                if result.hostname and device.hostname != result.hostname:
                    old_hostname = device.hostname
                    device.hostname = result.hostname
                    
                    activity = DeviceActivity.log_hostname_change(
                        device.id, old_hostname, result.hostname
                    )
                    db.add(activity)
                
                device.update_last_seen()
            
            scan_result = ScanResult(
                device_id=device.id,
                ip_address=result.ip_address,
                rssi=None,
                response_time_ms=result.response_time_ms,
                is_connected=True
            )
            db.add(scan_result)
            
            await notification_service.send_device_update(
                {"mac_address": device.mac_address, "is_new": is_new},
                "discovered" if is_new else "updated"
            )
        
        session.mark_completed(total_devices, new_devices)
        db.commit()
        
        await notification_service.send_scan_update({
            "status": "completed",
            "session_id": session_id,
            "total_devices": total_devices,
            "new_devices": new_devices
        })
        
        logger.info(f"Scan completed: {total_devices} devices, {new_devices} new")
        
    except Exception as e:
        logger.error(f"Scan failed: {e}")
        
        session = db.query(ScanSession).filter(ScanSession.id == session_id).first()
        if session:
            session.mark_failed(str(e))
            db.commit()
        
        await notification_service.send_scan_update({
            "status": "failed",
            "session_id": session_id,
            "error": str(e)
        })
    
    finally:
        _current_scan_session = None


@router.post("/start", response_model=ScanSessionResponse)
async def start_scan(
    scan_request: ScanRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start a new network scan."""
    global _current_scan_session
    
    if _current_scan_session and _current_scan_session.status == "running":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A scan is already in progress"
        )
    
    session = ScanSession(
        scan_type=scan_request.scan_type,
        network_range=scan_request.network_range or settings.DEFAULT_NETWORK_RANGE,
        status="running"
    )
    
    db.add(session)
    db.commit()
    db.refresh(session)
    
    _current_scan_session = session
    
    background_tasks.add_task(perform_scan, scan_request, session.id, db)
    
    logger.info(f"Scan started by {current_user.username}: {session.id}")
    
    return ScanSessionResponse(
        id=session.id,
        started_at=session.started_at,
        completed_at=session.completed_at,
        total_devices_found=session.total_devices_found,
        new_devices_found=session.new_devices_found,
        scan_type=session.scan_type,
        network_range=session.network_range,
        status=session.status,
        error_message=session.error_message,
        duration_seconds=session.duration_seconds
    )


@router.get("/status", response_model=ScanStatusResponse)
async def get_scan_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current scan status."""
    global _current_scan_session
    
    is_scanning = _current_scan_session is not None and _current_scan_session.status == "running"
    
    last_session = db.query(ScanSession).filter(
        ScanSession.status == "completed"
    ).order_by(ScanSession.completed_at.desc()).first()
    
    current_session = None
    if _current_scan_session:
        current_session = ScanSessionResponse(
            id=_current_scan_session.id,
            started_at=_current_scan_session.started_at,
            completed_at=_current_scan_session.completed_at,
            total_devices_found=_current_scan_session.total_devices_found,
            new_devices_found=_current_scan_session.new_devices_found,
            scan_type=_current_scan_session.scan_type,
            network_range=_current_scan_session.network_range,
            status=_current_scan_session.status,
            error_message=_current_scan_session.error_message,
            duration_seconds=_current_scan_session.duration_seconds
        )
    
    return ScanStatusResponse(
        is_scanning=is_scanning,
        current_session=current_session,
        last_scan_time=last_session.completed_at if last_session else None,
        next_scheduled_scan=None,
        devices_found_in_current_scan=_current_scan_session.total_devices_found if _current_scan_session else 0
    )


@router.get("/history")
async def get_scan_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get scan history."""
    total = db.query(ScanSession).count()
    
    offset = (page - 1) * page_size
    sessions = db.query(ScanSession).order_by(
        ScanSession.started_at.desc()
    ).offset(offset).limit(page_size).all()
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "sessions": [
            ScanSessionResponse(
                id=s.id,
                started_at=s.started_at,
                completed_at=s.completed_at,
                total_devices_found=s.total_devices_found,
                new_devices_found=s.new_devices_found,
                scan_type=s.scan_type,
                network_range=s.network_range,
                status=s.status,
                error_message=s.error_message,
                duration_seconds=s.duration_seconds
            ) for s in sessions
        ]
    }


@router.get("/results/{session_id}")
async def get_scan_results(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get results for a specific scan session."""
    session = db.query(ScanSession).filter(ScanSession.id == session_id).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan session not found"
        )
    
    results = db.query(ScanResult).filter(
        ScanResult.scan_timestamp >= session.started_at,
        ScanResult.scan_timestamp <= (session.completed_at or datetime.utcnow())
    ).all()
    
    return {
        "session": ScanSessionResponse(
            id=session.id,
            started_at=session.started_at,
            completed_at=session.completed_at,
            total_devices_found=session.total_devices_found,
            new_devices_found=session.new_devices_found,
            scan_type=session.scan_type,
            network_range=session.network_range,
            status=session.status,
            error_message=session.error_message,
            duration_seconds=session.duration_seconds
        ),
        "results": [r.to_dict() for r in results]
    }
