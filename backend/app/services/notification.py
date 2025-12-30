"""
Notification Service - Alert delivery via multiple channels.
"""

import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any, List
from datetime import datetime
import asyncio
import logging

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class NotificationService:
    """Service for sending notifications via various channels."""
    
    def __init__(self):
        self.email_enabled = settings.EMAIL_ENABLED
        self.webhook_url = settings.WEBHOOK_URL
        self.websocket_clients: List[Any] = []
    
    async def send_alert(self, alert: Dict[str, Any]):
        """Send alert through all configured channels."""
        tasks = []
        
        tasks.append(self.broadcast_websocket(alert))
        
        if self.email_enabled and settings.ALERT_EMAIL:
            tasks.append(self.send_email_alert(alert))
        
        if self.webhook_url:
            tasks.append(self.send_webhook(alert))
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def broadcast_websocket(self, data: Dict[str, Any]):
        """Broadcast message to all connected WebSocket clients."""
        message = json.dumps({
            "type": "alert",
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        disconnected = []
        for client in self.websocket_clients:
            try:
                await client.send_text(message)
            except Exception as e:
                logger.debug(f"WebSocket send failed: {e}")
                disconnected.append(client)
        
        for client in disconnected:
            self.websocket_clients.remove(client)
    
    def register_websocket(self, websocket):
        """Register a WebSocket client."""
        if websocket not in self.websocket_clients:
            self.websocket_clients.append(websocket)
            logger.info(f"WebSocket client registered. Total: {len(self.websocket_clients)}")
    
    def unregister_websocket(self, websocket):
        """Unregister a WebSocket client."""
        if websocket in self.websocket_clients:
            self.websocket_clients.remove(websocket)
            logger.info(f"WebSocket client unregistered. Total: {len(self.websocket_clients)}")
    
    async def send_email_alert(self, alert: Dict[str, Any]):
        """Send alert via email."""
        if not self.email_enabled:
            return
        
        try:
            subject = f"[WiFi Tracker] {alert.get('severity', 'INFO').upper()}: {alert.get('alert_type', 'Alert')}"
            
            body = f"""
WiFi Tracker Alert

Type: {alert.get('alert_type', 'Unknown')}
Severity: {alert.get('severity', 'Unknown')}
Time: {datetime.utcnow().isoformat()}

Message:
{alert.get('message', 'No message')}

Details:
{json.dumps(alert.get('details', {}), indent=2)}

---
WiFi Tracker System
            """
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._send_email, subject, body)
            
            logger.info(f"Email alert sent: {subject}")
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
    
    def _send_email(self, subject: str, body: str):
        """Synchronous email sending."""
        msg = MIMEMultipart()
        msg['From'] = settings.SMTP_USER
        msg['To'] = settings.ALERT_EMAIL
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
    
    async def send_webhook(self, alert: Dict[str, Any]):
        """Send alert to webhook URL."""
        if not self.webhook_url or not REQUESTS_AVAILABLE:
            return
        
        try:
            payload = {
                "event": "wifi_tracker_alert",
                "timestamp": datetime.utcnow().isoformat(),
                "alert": alert
            }
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None, 
                lambda: requests.post(
                    self.webhook_url,
                    json=payload,
                    timeout=10,
                    headers={"Content-Type": "application/json"}
                )
            )
            
            logger.info(f"Webhook alert sent to {self.webhook_url}")
            
        except Exception as e:
            logger.error(f"Failed to send webhook: {e}")
    
    async def send_device_update(self, device: Dict[str, Any], event: str):
        """Broadcast device update to WebSocket clients."""
        message = json.dumps({
            "type": "device_update",
            "event": event,
            "data": device,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        for client in self.websocket_clients:
            try:
                await client.send_text(message)
            except Exception:
                pass
    
    async def send_scan_update(self, scan_data: Dict[str, Any]):
        """Broadcast scan progress/results to WebSocket clients."""
        message = json.dumps({
            "type": "scan_update",
            "data": scan_data,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        for client in self.websocket_clients:
            try:
                await client.send_text(message)
            except Exception:
                pass


notification_service = NotificationService()
