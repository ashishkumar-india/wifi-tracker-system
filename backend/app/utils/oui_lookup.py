"""
OUI (Organizationally Unique Identifier) lookup for MAC vendor identification.
"""

import re
from pathlib import Path
from typing import Optional, Dict
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class OUILookup:
    """MAC address vendor lookup using OUI database."""
    
    _instance = None
    _oui_data: Dict[str, str] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_oui_database()
        return cls._instance
    
    def _load_oui_database(self):
        """Load OUI database from file or create default."""
        oui_path = settings.OUI_DATABASE_PATH
        
        if oui_path.exists():
            try:
                self._parse_oui_file(oui_path)
                logger.info(f"Loaded {len(self._oui_data)} OUI entries")
            except Exception as e:
                logger.error(f"Failed to load OUI database: {e}")
                self._load_default_oui()
        else:
            logger.warning("OUI database not found, using defaults")
            self._load_default_oui()
    
    def _parse_oui_file(self, path: Path):
        """Parse IEEE OUI file format."""
        pattern = re.compile(r'^([0-9A-F]{2}-[0-9A-F]{2}-[0-9A-F]{2})\s+\(hex\)\s+(.+)$')
        
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                match = pattern.match(line.strip())
                if match:
                    oui = match.group(1).replace('-', ':')
                    vendor = match.group(2).strip()
                    self._oui_data[oui.upper()] = vendor
    
    def _load_default_oui(self):
        """Load common vendor prefixes as fallback."""
        self._oui_data = {
            "00:00:0C": "Cisco Systems",
            "00:1A:2B": "Ayecom Technology",
            "00:50:56": "VMware",
            "08:00:27": "Oracle VirtualBox",
            "00:0C:29": "VMware",
            "00:1C:42": "Parallels",
            "00:03:FF": "Microsoft Hyper-V",
            "00:15:5D": "Microsoft Hyper-V",
            "DC:A6:32": "Raspberry Pi",
            "B8:27:EB": "Raspberry Pi",
            "E4:5F:01": "Raspberry Pi",
            "28:CD:C1": "Raspberry Pi",
            "00:1B:21": "Intel",
            "00:1E:67": "Intel",
            "3C:97:0E": "Intel",
            "AC:DE:48": "Intel",
            "18:31:BF": "ASUSTek",
            "00:1F:C6": "ASUSTek",
            "00:23:54": "ASUSTek",
            "00:1D:60": "ASUSTek",
            "00:25:22": "ASRock",
            "BC:5F:F4": "ASRock",
            "00:24:8C": "ASUSTek",
            "00:E0:4C": "Realtek",
            "52:54:00": "QEMU",
            "00:1A:A0": "Dell",
            "14:FE:B5": "Dell",
            "00:14:22": "Dell",
            "D4:BE:D9": "Dell",
            "00:21:9B": "Dell",
            "3C:D9:2B": "HP",
            "00:1E:0B": "HP",
            "00:21:5A": "HP",
            "D8:D3:85": "HP",
            "00:25:B3": "HP",
            "00:1F:29": "HP",
            "A4:5D:36": "HP",
            "00:0D:3A": "Microsoft",
            "28:18:78": "Microsoft",
            "60:45:BD": "Microsoft",
            "7C:1E:52": "Microsoft",
            "98:5F:D3": "Microsoft",
            "00:23:14": "Intel",
            "00:24:D7": "Intel",
            "00:26:C6": "Intel",
            "00:26:C7": "Intel",
            "A0:36:9F": "Intel",
            "3C:A9:F4": "Intel",
            "00:1B:63": "Apple",
            "00:1E:C2": "Apple",
            "00:25:00": "Apple",
            "00:26:08": "Apple",
            "00:26:B0": "Apple",
            "00:26:BB": "Apple",
            "28:CF:DA": "Apple",
            "34:C0:59": "Apple",
            "3C:D0:F8": "Apple",
            "7C:C5:37": "Apple",
            "88:63:DF": "Apple",
            "A4:B8:05": "Apple",
            "AC:BC:32": "Apple",
            "C8:BC:C8": "Apple",
            "D0:25:98": "Apple",
            "F0:B4:79": "Apple",
            "00:1A:11": "Google",
            "00:1A:2B": "Google",
            "3C:5A:B4": "Google",
            "94:EB:2C": "Google",
            "F4:F5:D8": "Google",
            "30:FD:38": "Google",
            "44:07:0B": "Google",
            "E8:B2:AC": "Apple",
            "00:1E:52": "Apple",
            "AC:87:A3": "Apple",
            "20:C9:D0": "Apple",
            "90:B0:ED": "Apple",
            "EC:85:2F": "TP-Link",
            "30:B5:C2": "TP-Link",
            "50:C7:BF": "TP-Link",
            "78:44:76": "TP-Link",
            "60:E3:27": "TP-Link",
            "14:CC:20": "TP-Link",
            "00:90:A9": "Western Digital",
            "00:01:42": "Cisco-Linksys",
            "00:12:17": "Cisco-Linksys",
            "00:18:39": "Cisco-Linksys",
            "00:1A:70": "Cisco-Linksys",
            "00:1C:10": "Cisco-Linksys",
            "00:1D:7E": "Cisco-Linksys",
            "00:1E:E5": "Cisco-Linksys",
            "00:21:29": "Cisco-Linksys",
            "00:22:6B": "Cisco-Linksys",
            "00:23:69": "Cisco-Linksys",
            "00:25:9C": "Cisco-Linksys",
            "20:AA:4B": "Cisco-Linksys",
            "00:22:75": "Belkin",
            "94:10:3E": "Belkin",
            "C0:56:27": "Belkin",
            "08:86:3B": "Belkin",
            "B4:75:0E": "Belkin",
            "00:1F:33": "Netgear",
            "00:22:3F": "Netgear",
            "00:24:B2": "Netgear",
            "00:26:F2": "Netgear",
            "20:4E:7F": "Netgear",
            "A0:21:B7": "Netgear",
            "C0:3F:0E": "Netgear",
            "C4:04:15": "Netgear",
            "04:A1:51": "Netgear",
            "30:46:9A": "Netgear",
            "44:94:FC": "Netgear",
            "28:C6:8E": "Netgear",
            "E0:91:F5": "Netgear",
            "00:14:6C": "Netgear",
            "00:09:5B": "Netgear",
            "00:0F:B5": "Netgear",
            "00:18:4D": "Netgear",
            "00:1B:2F": "Netgear",
            "00:1E:2A": "Netgear",
            "30:B4:9E": "TP-Link",
            "14:91:82": "Belkin",
            "EC:1A:59": "Belkin",
            "80:69:33": "Belkin",
            "B4:52:7E": "Samsung",
            "00:12:47": "Samsung",
            "00:13:77": "Samsung",
            "00:15:B9": "Samsung",
            "00:16:32": "Samsung",
            "00:17:C9": "Samsung",
            "00:18:AF": "Samsung",
            "00:1A:8A": "Samsung",
            "00:1B:98": "Samsung",
            "00:1C:43": "Samsung",
            "00:1D:25": "Samsung",
            "00:1D:F6": "Samsung",
            "00:1E:7D": "Samsung",
            "00:1F:CC": "Samsung",
            "00:21:19": "Samsung",
            "00:21:D1": "Samsung",
            "00:23:39": "Samsung",
            "00:23:99": "Samsung",
            "00:23:D6": "Samsung",
            "00:24:54": "Samsung",
            "00:24:90": "Samsung",
            "00:24:91": "Samsung",
            "00:24:E9": "Samsung",
            "00:25:38": "Samsung",
            "00:25:66": "Samsung",
            "00:25:67": "Samsung",
            "00:26:37": "Samsung",
            "00:26:5D": "Samsung",
            "00:26:5F": "Samsung",
            "5C:0A:5B": "Samsung",
            "64:B3:10": "Samsung",
            "84:38:38": "Samsung",
            "A0:B4:A5": "Samsung",
            "C4:73:1E": "Samsung"
        }
    
    def lookup(self, mac_address: str) -> Optional[str]:
        """Look up vendor for MAC address."""
        if not mac_address:
            return None
        
        mac = mac_address.upper().replace('-', ':')
        oui = mac[:8]
        
        return self._oui_data.get(oui)
    
    def get_device_type(self, vendor: str) -> Optional[str]:
        """Guess device type based on vendor."""
        if not vendor:
            return "Unknown"
        
        vendor_lower = vendor.lower()
        
        if any(x in vendor_lower for x in ['apple', 'iphone', 'ipad']):
            return "Mobile/Tablet"
        elif any(x in vendor_lower for x in ['samsung', 'lg', 'huawei', 'xiaomi', 'oneplus', 'oppo', 'vivo']):
            return "Mobile"
        elif any(x in vendor_lower for x in ['intel', 'dell', 'hp', 'lenovo', 'asus', 'acer', 'microsoft']):
            return "Computer"
        elif any(x in vendor_lower for x in ['cisco', 'netgear', 'tp-link', 'linksys', 'd-link', 'belkin', 'zyxel']):
            return "Network Device"
        elif any(x in vendor_lower for x in ['vmware', 'virtualbox', 'qemu', 'hyper-v', 'parallels']):
            return "Virtual Machine"
        elif any(x in vendor_lower for x in ['raspberry', 'arduino', 'espressif']):
            return "IoT Device"
        elif any(x in vendor_lower for x in ['amazon', 'google', 'nest', 'ring', 'philips hue']):
            return "Smart Home"
        elif any(x in vendor_lower for x in ['western digital', 'seagate', 'synology', 'qnap']):
            return "Storage"
        elif any(x in vendor_lower for x in ['roku', 'chromecast', 'fire tv', 'nvidia shield']):
            return "Streaming Device"
        elif any(x in vendor_lower for x in ['canon', 'epson', 'hp', 'brother']):
            return "Printer"
        elif any(x in vendor_lower for x in ['sony', 'nintendo', 'microsoft xbox', 'playstation']):
            return "Gaming Console"
        
        return "Unknown"


oui_lookup = OUILookup()
