"""
Signal Strength Analyzer - RSSI collection and quality metrics.
"""

import subprocess
import platform
import re
from typing import Optional, Dict, List, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

from app.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class SignalMetrics:
    """Signal strength metrics."""
    rssi: Optional[int]
    quality_percent: Optional[int]
    noise_level: Optional[int]
    link_speed: Optional[str]
    frequency: Optional[str]
    channel: Optional[int]


class SignalAnalyzer:
    """Analyze WiFi signal strength and quality."""
    
    def __init__(self):
        self.is_windows = platform.system().lower() == 'windows'
        self.signal_history: Dict[str, List[Dict]] = {}
    
    def get_wifi_signal_info(self) -> Optional[SignalMetrics]:
        """Get current WiFi signal information from local adapter."""
        try:
            if self.is_windows:
                return self._get_windows_signal()
            else:
                return self._get_linux_signal()
        except Exception as e:
            logger.error(f"Failed to get signal info: {e}")
            return None
    
    def _get_windows_signal(self) -> Optional[SignalMetrics]:
        """Get WiFi signal on Windows using netsh."""
        try:
            output = subprocess.check_output(
                "netsh wlan show interfaces",
                shell=True
            ).decode('utf-8', errors='ignore')
            
            rssi = None
            quality = None
            channel = None
            frequency = None
            link_speed = None
            
            for line in output.split('\n'):
                line = line.strip()
                
                if 'Signal' in line and '%' in line:
                    match = re.search(r'(\d+)%', line)
                    if match:
                        quality = int(match.group(1))
                        rssi = self._quality_to_rssi(quality)
                
                if 'Channel' in line:
                    match = re.search(r':\s*(\d+)', line)
                    if match:
                        channel = int(match.group(1))
                
                if 'Radio type' in line:
                    if '5 GHz' in line or '5GHz' in line:
                        frequency = "5 GHz"
                    elif '2.4 GHz' in line or '2.4GHz' in line:
                        frequency = "2.4 GHz"
                
                if 'Receive rate' in line or 'Transmit rate' in line:
                    match = re.search(r'(\d+\.?\d*)\s*(Mbps|Gbps)', line)
                    if match and not link_speed:
                        link_speed = f"{match.group(1)} {match.group(2)}"
            
            return SignalMetrics(
                rssi=rssi,
                quality_percent=quality,
                noise_level=None,
                link_speed=link_speed,
                frequency=frequency,
                channel=channel
            )
            
        except Exception as e:
            logger.error(f"Windows signal detection failed: {e}")
            return None
    
    def _get_linux_signal(self) -> Optional[SignalMetrics]:
        """Get WiFi signal on Linux using iwconfig/iw."""
        try:
            output = subprocess.check_output(
                "iwconfig 2>/dev/null || iw dev 2>/dev/null",
                shell=True
            ).decode('utf-8', errors='ignore')
            
            rssi = None
            quality = None
            noise = None
            channel = None
            frequency = None
            link_speed = None
            
            signal_match = re.search(r'Signal level[=:]?\s*(-?\d+)\s*dBm', output)
            if signal_match:
                rssi = int(signal_match.group(1))
                quality = self._rssi_to_quality(rssi)
            
            quality_match = re.search(r'Link Quality[=:]?\s*(\d+)/(\d+)', output)
            if quality_match:
                curr = int(quality_match.group(1))
                max_val = int(quality_match.group(2))
                quality = int((curr / max_val) * 100)
            
            noise_match = re.search(r'Noise level[=:]?\s*(-?\d+)\s*dBm', output)
            if noise_match:
                noise = int(noise_match.group(1))
            
            freq_match = re.search(r'Frequency[=:]?\s*(\d+\.?\d*)\s*GHz', output)
            if freq_match:
                freq = float(freq_match.group(1))
                frequency = f"{freq} GHz"
            
            rate_match = re.search(r'Bit Rate[=:]?\s*(\d+\.?\d*)\s*(Mb/s|Gb/s)', output)
            if rate_match:
                link_speed = f"{rate_match.group(1)} {rate_match.group(2)}"
            
            return SignalMetrics(
                rssi=rssi,
                quality_percent=quality,
                noise_level=noise,
                link_speed=link_speed,
                frequency=frequency,
                channel=channel
            )
            
        except Exception as e:
            logger.error(f"Linux signal detection failed: {e}")
            return None
    
    def record_signal(self, mac_address: str, rssi: int):
        """Record signal strength for historical analysis."""
        if mac_address not in self.signal_history:
            self.signal_history[mac_address] = []
        
        self.signal_history[mac_address].append({
            "timestamp": datetime.utcnow(),
            "rssi": rssi
        })
        
        cutoff = datetime.utcnow() - timedelta(hours=24)
        self.signal_history[mac_address] = [
            r for r in self.signal_history[mac_address]
            if r["timestamp"] > cutoff
        ]
    
    def get_signal_stats(self, mac_address: str) -> Dict[str, Any]:
        """Get signal statistics for a device."""
        history = self.signal_history.get(mac_address, [])
        
        if not history:
            return {
                "samples": 0,
                "avg_rssi": None,
                "min_rssi": None,
                "max_rssi": None,
                "variance": None,
                "trend": None
            }
        
        rssi_values = [r["rssi"] for r in history if r["rssi"] is not None]
        
        if not rssi_values:
            return {"samples": 0}
        
        avg_rssi = sum(rssi_values) / len(rssi_values)
        min_rssi = min(rssi_values)
        max_rssi = max(rssi_values)
        variance = sum((x - avg_rssi) ** 2 for x in rssi_values) / len(rssi_values)
        
        trend = None
        if len(rssi_values) >= 5:
            recent = rssi_values[-5:]
            older = rssi_values[:5]
            if sum(recent) / 5 > sum(older) / 5 + 3:
                trend = "improving"
            elif sum(recent) / 5 < sum(older) / 5 - 3:
                trend = "degrading"
            else:
                trend = "stable"
        
        return {
            "samples": len(rssi_values),
            "avg_rssi": round(avg_rssi, 1),
            "min_rssi": min_rssi,
            "max_rssi": max_rssi,
            "variance": round(variance, 2),
            "trend": trend,
            "quality": self._rssi_to_quality(int(avg_rssi))
        }
    
    @staticmethod
    def _rssi_to_quality(rssi: int) -> int:
        """Convert RSSI (dBm) to quality percentage."""
        if rssi >= -50:
            return 100
        elif rssi >= -60:
            return 80 + (rssi + 60) * 2
        elif rssi >= -70:
            return 60 + (rssi + 70) * 2
        elif rssi >= -80:
            return 40 + (rssi + 80) * 2
        elif rssi >= -90:
            return 20 + (rssi + 90) * 2
        else:
            return max(0, 10 + (rssi + 100))
    
    @staticmethod
    def _quality_to_rssi(quality: int) -> int:
        """Estimate RSSI from quality percentage."""
        if quality >= 100:
            return -50
        elif quality >= 80:
            return -60 + (quality - 80) // 2
        elif quality >= 60:
            return -70 + (quality - 60) // 2
        elif quality >= 40:
            return -80 + (quality - 40) // 2
        elif quality >= 20:
            return -90 + (quality - 20) // 2
        else:
            return -100 + quality
    
    @staticmethod
    def get_signal_quality_label(rssi: int) -> str:
        """Get human-readable signal quality label."""
        if rssi >= -50:
            return "Excellent"
        elif rssi >= -60:
            return "Good"
        elif rssi >= -70:
            return "Fair"
        elif rssi >= -80:
            return "Weak"
        else:
            return "Poor"


signal_analyzer = SignalAnalyzer()
