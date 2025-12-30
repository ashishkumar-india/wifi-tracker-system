"""
Alerts router - Alert management endpoints.
"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.database import get_db
from app.models.alert import Alert, AlertType, AlertSeverity
from app.models.device import Device
from app.models.user import User
from app.schemas.alert import (
    AlertResponse, AlertListResponse, AlertAcknowledge, AlertStats, DeviceInfo
)
from app.routers.auth import get_current_user
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/alerts", tags=["Alerts"])


def get_enum_value(value):
    """Safely get value from enum or return string as-is."""
    if hasattr(value, 'value'):
        return value.value
    return str(value) if value else None


@router.get("", response_model=AlertListResponse)
async def list_alerts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    alert_type: Optional[str] = None,
    severity: Optional[str] = None,
    is_acknowledged: Optional[bool] = None,
    device_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all alerts with filtering."""
    query = db.query(Alert)
    
    if alert_type:
        try:
            query = query.filter(Alert.alert_type == AlertType(alert_type))
        except ValueError:
            pass
    
    if severity:
        try:
            query = query.filter(Alert.severity == AlertSeverity(severity))
        except ValueError:
            pass
    
    if is_acknowledged is not None:
        query = query.filter(Alert.is_acknowledged == is_acknowledged)
    
    if device_id:
        query = query.filter(Alert.device_id == device_id)
    
    total = query.count()
    
    unacknowledged = db.query(Alert).filter(Alert.is_acknowledged == False).count()
    
    query = query.order_by(Alert.created_at.desc())
    
    offset = (page - 1) * page_size
    alerts = query.offset(offset).limit(page_size).all()
    
    alert_responses = []
    for alert in alerts:
        device_info = None
        if alert.device:
            device_info = DeviceInfo(
                mac_address=alert.device.mac_address,
                hostname=alert.device.hostname,
                vendor=alert.device.vendor
            )
        
        ack_username = None
        if alert.acknowledged_by_user:
            ack_username = alert.acknowledged_by_user.username
        
        alert_responses.append(AlertResponse(
            id=alert.id,
            device_id=alert.device_id,
            alert_type=get_enum_value(alert.alert_type),
            severity=get_enum_value(alert.severity),
            message=alert.message,
            details=alert.details,
            is_acknowledged=alert.is_acknowledged,
            acknowledged_by=alert.acknowledged_by,
            acknowledged_by_username=ack_username,
            created_at=alert.created_at,
            acknowledged_at=alert.acknowledged_at,
            device=device_info
        ))
    
    return AlertListResponse(
        total=total,
        page=page,
        page_size=page_size,
        unacknowledged_count=unacknowledged,
        alerts=alert_responses
    )


@router.get("/stats", response_model=AlertStats)
async def get_alert_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get alert statistics."""
    total = db.query(Alert).count()
    unacknowledged = db.query(Alert).filter(Alert.is_acknowledged == False).count()
    
    by_severity = {}
    severity_counts = db.query(
        Alert.severity, func.count(Alert.id)
    ).group_by(Alert.severity).all()
    
    for severity, count in severity_counts:
        by_severity[get_enum_value(severity)] = count
    
    by_type = {}
    type_counts = db.query(
        Alert.alert_type, func.count(Alert.id)
    ).group_by(Alert.alert_type).all()
    
    for alert_type, count in type_counts:
        by_type[get_enum_value(alert_type)] = count
    
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    alerts_today = db.query(Alert).filter(Alert.created_at >= today).count()
    
    week_ago = today - timedelta(days=7)
    alerts_this_week = db.query(Alert).filter(Alert.created_at >= week_ago).count()
    
    return AlertStats(
        total_alerts=total,
        unacknowledged=unacknowledged,
        by_severity=by_severity,
        by_type=by_type,
        alerts_today=alerts_today,
        alerts_this_week=alerts_this_week
    )


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get alert details."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    device_info = None
    if alert.device:
        device_info = DeviceInfo(
            mac_address=alert.device.mac_address,
            hostname=alert.device.hostname,
            vendor=alert.device.vendor
        )
    
    ack_username = None
    if alert.acknowledged_by_user:
        ack_username = alert.acknowledged_by_user.username
    
    return AlertResponse(
        id=alert.id,
        device_id=alert.device_id,
        alert_type=get_enum_value(alert.alert_type),
        severity=get_enum_value(alert.severity),
        message=alert.message,
        details=alert.details,
        is_acknowledged=alert.is_acknowledged,
        acknowledged_by=alert.acknowledged_by,
        acknowledged_by_username=ack_username,
        created_at=alert.created_at,
        acknowledged_at=alert.acknowledged_at,
        device=device_info
    )


@router.put("/{alert_id}/acknowledge", response_model=AlertResponse)
async def acknowledge_alert(
    alert_id: int,
    ack_data: AlertAcknowledge = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Acknowledge an alert."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    if alert.is_acknowledged:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Alert already acknowledged"
        )
    
    alert.acknowledge(current_user.id)
    
    db.commit()
    db.refresh(alert)
    
    logger.info(f"Alert {alert_id} acknowledged by {current_user.username}")
    
    device_info = None
    if alert.device:
        device_info = DeviceInfo(
            mac_address=alert.device.mac_address,
            hostname=alert.device.hostname,
            vendor=alert.device.vendor
        )
    
    return AlertResponse(
        id=alert.id,
        device_id=alert.device_id,
        alert_type=get_enum_value(alert.alert_type),
        severity=get_enum_value(alert.severity),
        message=alert.message,
        details=alert.details,
        is_acknowledged=alert.is_acknowledged,
        acknowledged_by=alert.acknowledged_by,
        acknowledged_by_username=current_user.username,
        created_at=alert.created_at,
        acknowledged_at=alert.acknowledged_at,
        device=device_info
    )


@router.post("/acknowledge-all", status_code=status.HTTP_200_OK)
async def acknowledge_all_alerts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Acknowledge all unacknowledged alerts."""
    now = datetime.utcnow()
    
    result = db.query(Alert).filter(
        Alert.is_acknowledged == False
    ).update({
        Alert.is_acknowledged: True,
        Alert.acknowledged_by: current_user.id,
        Alert.acknowledged_at: now
    })
    
    db.commit()
    
    logger.info(f"{result} alerts acknowledged by {current_user.username}")
    
    return {"acknowledged_count": result}


@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an alert."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    db.delete(alert)
    db.commit()
    
    logger.info(f"Alert {alert_id} deleted by {current_user.username}")
