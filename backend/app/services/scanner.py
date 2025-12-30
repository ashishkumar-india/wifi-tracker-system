"""
Network Scanner Module - ARP and ICMP scanning for device discovery.
Requires administrator/root privileges.
"""

import socket
import subprocess
import platform
import ipaddress
import asyncio
import time
import sys
import os
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import logging

# Suppress Scapy's warnings (libpcap, OUI database) by temporarily redirecting stderr
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=".*libpcap.*")
warnings.filterwarnings("ignore", message=".*OUI.*")

_stderr_backup = sys.stderr
_stdout_backup = sys.stdout
SCAPY_AVAILABLE = False

try:
    # Redirect both stdout and stderr to /dev/null during import
    _devnull = open(os.devnull, 'w')
    sys.stderr = _devnull
    sys.stdout = _devnull
    
    # Suppress Scapy loggers before import
    logging.getLogger("scapy").setLevel(logging.CRITICAL)
    logging.getLogger("scapy.runtime").setLevel(logging.CRITICAL)
    
    # Import Scapy components
    from scapy.all import ARP, Ether, srp, conf
    SCAPY_AVAILABLE = True
    
except ImportError:
    pass
except Exception:
    pass
finally:
    # Always restore stdout and stderr
    sys.stderr = _stderr_backup
    sys.stdout = _stdout_backup
    try:
        _devnull.close()
    except:
        pass

# Check if pcap is available for layer 2 operations
PCAP_AVAILABLE = False
if SCAPY_AVAILABLE:
    try:
        from scapy.arch import get_if_list
        # Try to check if we can actually use layer 2
        conf.verb = 0
        # On Windows, check if Npcap/WinPcap is installed
        if platform.system().lower() == 'windows':
            try:
                from scapy.arch.windows import get_windows_if_list
                # If we can get interface list without error, pcap might be available
                ifaces = get_windows_if_list()
                if ifaces:
                    PCAP_AVAILABLE = True
            except Exception:
                pass
        else:
            # On Linux/Mac, pcap is usually available
            PCAP_AVAILABLE = True
    except Exception:
        pass

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Log pcap status once at module load
if SCAPY_AVAILABLE and not PCAP_AVAILABLE:
    logger.info("Npcap/WinPcap not detected - using fallback scanning methods (ARP table + ping)")
elif SCAPY_AVAILABLE and PCAP_AVAILABLE:
    logger.info("Scapy with pcap support available - full scanning enabled")


@dataclass
class ScanResult:
    """Data class for scan results."""
    ip_address: str
    mac_address: str
    hostname: Optional[str] = None
    response_time_ms: Optional[float] = None
    is_alive: bool = True


class NetworkScanner:
    """Network scanner using ARP and ICMP protocols."""
    
    def __init__(self, network_range: str = None, timeout: int = None):
        self.network_range = network_range or settings.DEFAULT_NETWORK_RANGE
        self.timeout = timeout or settings.SCAN_TIMEOUT
        self.max_workers = settings.MAX_CONCURRENT_SCANS
        self.is_windows = platform.system().lower() == 'windows'
        
        if SCAPY_AVAILABLE:
            conf.verb = 0
    
    def get_local_network_info(self) -> Dict[str, str]:
        """Get local network interface information."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            
            ip_parts = local_ip.split('.')
            network = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.0/24"
            
            return {
                "local_ip": local_ip,
                "network_range": network,
                "interface": "default"
            }
        except Exception as e:
            logger.error(f"Failed to get network info: {e}")
            return {
                "local_ip": "127.0.0.1",
                "network_range": self.network_range,
                "interface": "unknown"
            }
    
    def arp_scan(self, network_range: str = None) -> List[ScanResult]:
        """Perform ARP scan to discover devices on the network."""
        target = network_range or self.network_range
        results = []
        
        # Use fallback method if Scapy or pcap is not available
        if not SCAPY_AVAILABLE or not PCAP_AVAILABLE:
            logger.debug("Using fallback ARP table method")
            return self._get_arp_table_with_ping(target)
        
        try:
            logger.info(f"Starting ARP scan on {target}")
            start_time = time.time()
            
            arp_request = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=target)
            answered, _ = srp(arp_request, timeout=self.timeout, verbose=False)
            
            for sent, received in answered:
                try:
                    hostname = self._resolve_hostname(received.psrc)
                    response_time = (time.time() - start_time) * 1000
                    
                    results.append(ScanResult(
                        ip_address=received.psrc,
                        mac_address=received.hwsrc.upper(),
                        hostname=hostname,
                        response_time_ms=round(response_time, 2)
                    ))
                except Exception as e:
                    logger.debug(f"Error processing response: {e}")
            
            logger.info(f"ARP scan complete: {len(results)} devices found")
            
        except PermissionError:
            logger.warning("ARP scan requires administrator privileges, using fallback")
            return self._get_arp_table_with_ping(target)
        except Exception as e:
            logger.debug(f"ARP scan not available: {e}")
            return self._get_arp_table_with_ping(target)
        
        return results
    
    def _get_arp_table(self) -> List[ScanResult]:
        """Get devices from system ARP table (fallback method)."""
        results = []
        
        try:
            if self.is_windows:
                # Use full path to arp.exe on Windows
                output = subprocess.check_output(
                    [r"C:\Windows\System32\ARP.EXE", "-a"], 
                    stderr=subprocess.DEVNULL
                ).decode('utf-8', errors='ignore')
                for line in output.split('\n'):
                    parts = line.split()
                    if len(parts) >= 3:
                        ip = parts[0]
                        mac = parts[1].replace('-', ':').upper()
                        if self._is_valid_ip(ip) and self._is_valid_mac(mac):
                            hostname = self._resolve_hostname(ip)
                            results.append(ScanResult(
                                ip_address=ip,
                                mac_address=mac,
                                hostname=hostname
                            ))
            else:
                output = subprocess.check_output(["arp", "-n"]).decode('utf-8', errors='ignore')
                for line in output.split('\n')[1:]:
                    parts = line.split()
                    if len(parts) >= 3:
                        ip = parts[0]
                        mac = parts[2].upper()
                        if self._is_valid_ip(ip) and self._is_valid_mac(mac):
                            hostname = self._resolve_hostname(ip)
                            results.append(ScanResult(
                                ip_address=ip,
                                mac_address=mac,
                                hostname=hostname
                            ))
        except Exception as e:
            logger.error(f"Failed to read ARP table: {e}")
        
        return results
    
    def _get_arp_table_with_ping(self, network_range: str = None) -> List[ScanResult]:
        """
        Enhanced fallback method: ping sweep to populate ARP table, then read it.
        Works without Npcap/WinPcap installed.
        """
        target = network_range or self.network_range
        results = []
        seen_ips = set()
        
        try:
            logger.info(f"Starting fallback scan on {target} (ping + ARP table)")
            
            # First, do a quick ping sweep to populate the ARP table
            network = ipaddress.ip_network(target, strict=False)
            hosts = list(network.hosts())
            
            # Limit to first 254 hosts for /24 networks
            hosts = hosts[:254]
            
            # Quick parallel ping to populate ARP table
            with ThreadPoolExecutor(max_workers=min(50, len(hosts))) as executor:
                futures = []
                for host in hosts:
                    if self.is_windows:
                        cmd = f"ping -n 1 -w 500 {host}"
                    else:
                        cmd = f"ping -c 1 -W 1 {host}"
                    futures.append(executor.submit(
                        subprocess.run, 
                        cmd, 
                        shell=True, 
                        capture_output=True, 
                        timeout=2
                    ))
                
                # Wait for all pings to complete (they populate ARP cache)
                for future in futures:
                    try:
                        future.result(timeout=3)
                    except Exception:
                        pass
            
            # Now read the populated ARP table
            results = self._get_arp_table()
            
            # Also check which hosts are actually responding
            responding_hosts = []
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                ping_futures = {executor.submit(self._ping_host, str(host)): host for host in hosts}
                for future in ping_futures:
                    try:
                        result = future.result(timeout=5)
                        if result and result.ip_address not in seen_ips:
                            seen_ips.add(result.ip_address)
                            responding_hosts.append(result)
                    except Exception:
                        pass
            
            # Merge results - prefer ARP results (have MAC) but add ping-only results
            arp_ips = {r.ip_address for r in results}
            for host in responding_hosts:
                if host.ip_address not in arp_ips:
                    results.append(host)
            
            logger.info(f"Fallback scan complete: {len(results)} devices found")
            
        except Exception as e:
            logger.error(f"Fallback scan failed: {e}")
            # Last resort: just return ARP table
            results = self._get_arp_table()
        
        return results
    
    def icmp_scan(self, network_range: str = None) -> List[ScanResult]:
        """Perform ICMP ping scan to discover active hosts."""
        target = network_range or self.network_range
        results = []
        
        try:
            network = ipaddress.ip_network(target, strict=False)
            hosts = list(network.hosts())
            
            logger.info(f"Starting ICMP scan on {len(hosts)} hosts")
            
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {executor.submit(self._ping_host, str(host)): host for host in hosts}
                
                for future in futures:
                    result = future.result()
                    if result:
                        results.append(result)
            
            logger.info(f"ICMP scan complete: {len(results)} hosts responding")
            
        except Exception as e:
            logger.error(f"ICMP scan failed: {e}")
        
        return results
    
    def _ping_host(self, ip: str) -> Optional[ScanResult]:
        """Ping a single host and return result if alive."""
        try:
            if self.is_windows:
                cmd = f"ping -n 1 -w {self.timeout * 1000} {ip}"
            else:
                cmd = f"ping -c 1 -W {self.timeout} {ip}"
            
            start_time = time.time()
            result = subprocess.run(
                cmd, 
                shell=True, 
                capture_output=True, 
                timeout=self.timeout + 1
            )
            response_time = (time.time() - start_time) * 1000
            
            if result.returncode == 0:
                mac = self._get_mac_for_ip(ip)
                hostname = self._resolve_hostname(ip)
                
                return ScanResult(
                    ip_address=ip,
                    mac_address=mac or "00:00:00:00:00:00",
                    hostname=hostname,
                    response_time_ms=round(response_time, 2)
                )
        except subprocess.TimeoutExpired:
            pass
        except Exception as e:
            logger.debug(f"Ping failed for {ip}: {e}")
        
        return None
    
    def _get_mac_for_ip(self, ip: str) -> Optional[str]:
        """Get MAC address for an IP from ARP table."""
        try:
            if self.is_windows:
                output = subprocess.check_output(
                    [r"C:\Windows\System32\ARP.EXE", "-a", ip],
                    stderr=subprocess.DEVNULL
                ).decode('utf-8', errors='ignore')
                for line in output.split('\n'):
                    if ip in line:
                        parts = line.split()
                        if len(parts) >= 2:
                            mac = parts[1].replace('-', ':').upper()
                            if self._is_valid_mac(mac):
                                return mac
            else:
                output = subprocess.check_output(["arp", "-n", ip]).decode('utf-8', errors='ignore')
                for line in output.split('\n'):
                    if ip in line:
                        parts = line.split()
                        if len(parts) >= 3:
                            mac = parts[2].upper()
                            if self._is_valid_mac(mac):
                                return mac
        except Exception:
            pass
        return None
    
    def _resolve_hostname(self, ip: str) -> Optional[str]:
        """Resolve hostname for IP address."""
        try:
            hostname = socket.gethostbyaddr(ip)[0]
            return hostname
        except socket.herror:
            return None
        except Exception:
            return None
    
    def full_scan(self, network_range: str = None) -> List[ScanResult]:
        """Perform comprehensive scan combining ARP and ICMP."""
        target = network_range or self.network_range
        
        arp_results = self.arp_scan(target)
        icmp_results = self.icmp_scan(target)
        
        seen_ips = {r.ip_address for r in arp_results}
        for result in icmp_results:
            if result.ip_address not in seen_ips:
                arp_results.append(result)
        
        return arp_results
    
    @staticmethod
    def _is_valid_ip(ip: str) -> bool:
        """Validate IP address format."""
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def _is_valid_mac(mac: str) -> bool:
        """Validate MAC address format."""
        import re
        pattern = r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$'
        return bool(re.match(pattern, mac)) and mac != "00:00:00:00:00:00"
    
    async def async_arp_scan(self, network_range: str = None) -> List[ScanResult]:
        """Async wrapper for ARP scan."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.arp_scan, network_range)
    
    async def async_full_scan(self, network_range: str = None) -> List[ScanResult]:
        """Async wrapper for full scan."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.full_scan, network_range)
