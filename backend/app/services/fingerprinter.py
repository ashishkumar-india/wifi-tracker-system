"""
Device Fingerprinting Module - Identify devices by MAC, hostname, and behavior.
"""

import socket
import struct
from typing import Optional, Dict, Any
import logging

from app.utils.oui_lookup import oui_lookup
from app.utils.logger import get_logger

logger = get_logger(__name__)


class DeviceFingerprinter:
    """Device fingerprinting and identification service."""
    
    def __init__(self):
        self.oui_lookup = oui_lookup
    
    def fingerprint(self, mac_address: str, hostname: str = None, ip_address: str = None) -> Dict[str, Any]:
        """
        Create a device fingerprint from available information.
        
        Args:
            mac_address: Device MAC address
            hostname: Optional hostname
            ip_address: Optional IP address
            
        Returns:
            Dict with vendor, device_type, and confidence
        """
        fingerprint = {
            "mac_address": mac_address.upper() if mac_address else None,
            "vendor": None,
            "device_type": "Unknown",
            "os_guess": None,
            "hostname": hostname,
            "confidence": 0.0
        }
        
        if mac_address:
            fingerprint["vendor"] = self.oui_lookup.lookup(mac_address)
            if fingerprint["vendor"]:
                fingerprint["device_type"] = self.oui_lookup.get_device_type(fingerprint["vendor"])
                fingerprint["confidence"] += 0.3
        
        if hostname:
            hostname_info = self._analyze_hostname(hostname)
            fingerprint["os_guess"] = hostname_info.get("os_guess")
            
            if hostname_info.get("device_type"):
                if fingerprint["device_type"] == "Unknown":
                    fingerprint["device_type"] = hostname_info["device_type"]
                fingerprint["confidence"] += 0.2
        
        if mac_address:
            mac_info = self._analyze_mac_pattern(mac_address)
            if mac_info.get("is_local"):
                fingerprint["is_locally_administered"] = True
                fingerprint["confidence"] -= 0.1
        
        fingerprint["confidence"] = min(max(fingerprint["confidence"], 0.0), 1.0)
        
        return fingerprint
    
    def _analyze_hostname(self, hostname: str) -> Dict[str, Any]:
        """Analyze hostname for device/OS information."""
        result = {}
        hostname_lower = hostname.lower()
        
        os_patterns = {
            "windows": ["desktop-", "laptop-", "win-", "-pc", "windows"],
            "macos": ["macbook", "imac", "mac-", "macpro", "macmini"],
            "linux": ["linux", "ubuntu", "debian", "fedora", "centos", "raspberrypi"],
            "android": ["android", "galaxy", "pixel", "oneplus", "xiaomi", "redmi"],
            "ios": ["iphone", "ipad", "ipod"]
        }
        
        for os_name, patterns in os_patterns.items():
            if any(p in hostname_lower for p in patterns):
                result["os_guess"] = os_name
                break
        
        device_patterns = {
            "Mobile": ["iphone", "android", "phone", "galaxy", "pixel", "mobile"],
            "Tablet": ["ipad", "tablet", "tab"],
            "Computer": ["desktop", "laptop", "pc", "workstation", "macbook", "imac"],
            "Smart TV": ["tv", "roku", "firetv", "chromecast", "appletv"],
            "Printer": ["printer", "canon", "epson", "hp-", "brother"],
            "IoT Device": ["nest", "echo", "alexa", "google-home", "hue", "ring"],
            "Gaming Console": ["xbox", "playstation", "ps4", "ps5", "nintendo", "switch"]
        }
        
        for device_type, patterns in device_patterns.items():
            if any(p in hostname_lower for p in patterns):
                result["device_type"] = device_type
                break
        
        return result
    
    def _analyze_mac_pattern(self, mac_address: str) -> Dict[str, Any]:
        """Analyze MAC address patterns."""
        result = {}
        
        first_byte = int(mac_address.replace(":", "").replace("-", "")[:2], 16)
        result["is_local"] = bool(first_byte & 0x02)
        result["is_multicast"] = bool(first_byte & 0x01)
        
        return result
    
    def get_vendor(self, mac_address: str) -> Optional[str]:
        """Get vendor name for MAC address."""
        return self.oui_lookup.lookup(mac_address)
    
    def get_device_type(self, mac_address: str = None, vendor: str = None) -> str:
        """Get device type based on MAC or vendor."""
        if vendor:
            return self.oui_lookup.get_device_type(vendor)
        if mac_address:
            v = self.get_vendor(mac_address)
            if v:
                return self.oui_lookup.get_device_type(v)
        return "Unknown"
    
    def resolve_hostname(self, ip_address: str) -> Optional[str]:
        """Resolve hostname from IP address."""
        try:
            hostname = socket.gethostbyaddr(ip_address)[0]
            return hostname
        except (socket.herror, socket.gaierror):
            return None
        except Exception as e:
            logger.debug(f"Hostname resolution failed for {ip_address}: {e}")
            return None
    
    def get_netbios_name(self, ip_address: str, timeout: int = 2) -> Optional[str]:
        """Get NetBIOS name (Windows only)."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(timeout)
            
            request = (
                b'\x80\x94\x00\x00\x00\x01\x00\x00'
                b'\x00\x00\x00\x00\x20CKAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\x00\x00\x21\x00\x01'
            )
            
            sock.sendto(request, (ip_address, 137))
            
            try:
                data, _ = sock.recvfrom(1024)
                
                if len(data) > 57:
                    num_names = data[56]
                    if num_names > 0:
                        name_start = 57
                        name = data[name_start:name_start+15].decode('ascii', errors='ignore').strip()
                        return name
            except socket.timeout:
                pass
            finally:
                sock.close()
                
        except Exception as e:
            logger.debug(f"NetBIOS lookup failed for {ip_address}: {e}")
        
        return None


fingerprinter = DeviceFingerprinter()
