"""
Advanced Packet Capture Engine using Scapy
High-performance, multi-threaded packet capture with protocol parsing
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    from scapy.all import (
        sniff, get_if_list, conf, IP, TCP, UDP, ICMP, DNS, ARP, 
        Raw, Ether, IPv6, get_if_addr
    )
    from scapy.layers.http import HTTP, HTTPRequest, HTTPResponse
except ImportError as e:
    print(f"❌ Scapy not installed properly: {e}")
    print("Please run: pip install scapy scapy-http")
    sys.exit(1)

import threading
import queue
import time
import hashlib
import socket
from datetime import datetime
from typing import Optional, Callable, Dict, Any, List
import logging
import psutil
from collections import defaultdict
import json

# Import our models
from app.models.packet_model import PacketModel

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PacketCaptureEngine:
    """Advanced packet capture engine with multi-threading and protocol analysis"""
    
    def __init__(self, interface: Optional[str] = None, buffer_size: int = 10000):
        """Initialize the packet capture engine"""
        self.interface = interface or self._get_best_interface()
        self.buffer_size = buffer_size
        self.is_capturing = False
        self.packet_queue = queue.Queue(maxsize=buffer_size)
        self.capture_thread = None
        self.callback_functions = []
        
        # Statistics tracking
        self.stats = {
            'total_packets': 0,
            'dropped_packets': 0,
            'bytes_captured': 0,
            'start_time': None,
            'protocols': defaultdict(int),
            'packet_rates': [],
            'errors': 0
        }
        
        # Protocol parsers
        self.protocol_handlers = {
            'TCP': self._parse_tcp,
            'UDP': self._parse_udp,
            'ICMP': self._parse_icmp,
            'ARP': self._parse_arp,
            'IPv6': self._parse_ipv6
        }
        
        logger.info(f"🔧 Packet capture engine initialized")
        logger.info(f"📡 Selected interface: {self.interface}")
        logger.info(f"💾 Buffer size: {buffer_size} packets")
    
    def _get_best_interface(self) -> str:
        """Automatically select the best network interface"""
        try:
            interfaces = get_if_list()
            logger.info(f"📡 Available interfaces: {interfaces}")
            
            # Get network interface statistics
            net_stats = psutil.net_if_stats()
            
            # Preferred interface names (in order of preference)
            preferred_names = [
                'wlan0', 'wlo1', 'wlp', 'wifi',  # Wireless
                'eth0', 'en0', 'enp', 'eno',     # Ethernet  
                'WiFi', 'Ethernet', 'Wi-Fi'      # Windows
            ]
            
            # First, try preferred interfaces that are up
            for preferred in preferred_names:
                for iface in interfaces:
                    if preferred.lower() in iface.lower():
                        if iface in net_stats and net_stats[iface].isup:
                            try:
                                # Test if we can get IP address
                                ip = get_if_addr(iface)
                                if ip and ip != '127.0.0.1':
                                    logger.info(f"✅ Selected interface {iface} (IP: {ip})")
                                    return iface
                            except:
                                continue
            
            # Fallback: find any active interface with IP
            for iface in interfaces:
                if iface.lower() in ['lo', 'loopback']:
                    continue
                try:
                    if iface in net_stats and net_stats[iface].isup:
                        ip = get_if_addr(iface)
                        if ip and ip != '127.0.0.1':
                            logger.info(f"✅ Fallback interface {iface} (IP: {ip})")
                            return iface
                except:
                    continue
            
            # Last resort: return first non-loopback interface
            for iface in interfaces:
                if iface.lower() not in ['lo', 'lo0', 'loopback']:
                    logger.warning(f"⚠️ Using interface {iface} (may not be active)")
                    return iface
            
            # Very last resort
            if interfaces:
                return interfaces[0]
            else:
                raise Exception("No network interfaces found")
                
        except Exception as e:
            logger.error(f"❌ Error selecting interface: {e}")
            return 'eth0'  # Default fallback
    
    def add_callback(self, callback: Callable[[PacketModel], None]):
        """Add a callback function to be called for each packet"""
        self.callback_functions.append(callback)
        logger.info(f"📞 Added packet callback function")
    
    def start_capture(self, packet_filter: Optional[str] = None) -> bool:
        """Start packet capture in a separate thread"""
        if self.is_capturing:
            logger.warning("⚠️ Packet capture already in progress")
            return False
        
        try:
            self.is_capturing = True
            self.stats['start_time'] = datetime.now()
            self.stats['total_packets'] = 0
            self.stats['dropped_packets'] = 0
            self.stats['bytes_captured'] = 0
            
            logger.info(f"🚀 Starting packet capture on {self.interface}")
            if packet_filter:
                logger.info(f"🔍 Using filter: {packet_filter}")
            
            # Start capture thread
            self.capture_thread = threading.Thread(
                target=self._capture_loop,
                args=(packet_filter,),
                daemon=True,
                name="PacketCaptureThread"
            )
            self.capture_thread.start()
            
            # Start statistics thread
            stats_thread = threading.Thread(
                target=self._stats_loop,
                daemon=True,
                name="StatsThread"
            )
            stats_thread.start()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start packet capture: {e}")
            self.is_capturing = False
            return False
    
    def stop_capture(self) -> bool:
        """Stop packet capture gracefully"""
        if not self.is_capturing:
            logger.warning("⚠️ Packet capture is not running")
            return False
        
        try:
            logger.info("🛑 Stopping packet capture...")
            self.is_capturing = False
            
            # Wait for capture thread to finish
            if self.capture_thread and self.capture_thread.is_alive():
                self.capture_thread.join(timeout=5)
            
            logger.info("✅ Packet capture stopped successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error stopping packet capture: {e}")
            return False
    
    def _capture_loop(self, packet_filter: Optional[str] = None):
        """Main packet capture loop"""
        try:
            logger.info("👁️ Starting packet sniffing...")
            
            sniff(
                iface=self.interface,
                filter=packet_filter,
                prn=self._packet_handler,
                stop_filter=lambda pkt: not self.is_capturing,
                store=False,  # Don't store packets in memory
                timeout=1     # Check stop condition every second
            )
            
        except Exception as e:
            logger.error(f"❌ Packet capture error: {e}")
            self.stats['errors'] += 1
        finally:
            self.is_capturing = False
            logger.info("🔄 Packet capture loop ended")
    
    def _packet_handler(self, packet):
        """Process each captured packet"""
        try:
            # Update basic statistics
            self.stats['total_packets'] += 1
            self.stats['bytes_captured'] += len(packet)
            
            # Parse packet into our model
            packet_model = self._parse_packet(packet)
            if not packet_model:
                return
            
            # Update protocol statistics
            self.stats['protocols'][packet_model.protocol] += 1
            
            # Add to processing queue
            try:
                self.packet_queue.put_nowait(packet_model)
            except queue.Full:
                self.stats['dropped_packets'] += 1
                if self.stats['dropped_packets'] % 1000 == 0:
                    logger.warning(f"⚠️ Dropped {self.stats['dropped_packets']} packets due to full buffer")
            
            # Call all registered callbacks
            for callback in self.callback_functions:
                try:
                    callback(packet_model)
                except Exception as e:
                    logger.error(f"❌ Error in packet callback: {e}")
            
        except Exception as e:
            logger.error(f"❌ Error processing packet: {e}")
            self.stats['errors'] += 1
    
    def _parse_packet(self, packet) -> Optional[PacketModel]:
        """Parse a Scapy packet into our PacketModel"""
        try:
            packet_data = {
                'timestamp': datetime.now(),
                'packet_size': len(packet),
                'protocol': 'Unknown'
            }
            
            # Parse Ethernet layer
            if Ether in packet:
                eth_layer = packet[Ether]
                packet_data['eth_src'] = eth_layer.src
                packet_data['eth_dst'] = eth_layer.dst
            
            # Parse IP layer (IPv4)
            if IP in packet:
                ip_layer = packet[IP]
                packet_data.update({
                    'src_ip': ip_layer.src,
                    'dst_ip': ip_layer.dst,
                    'ttl': ip_layer.ttl,
                    'fragment_offset': ip_layer.frag,
                    'checksum': str(ip_layer.chksum)
                })
                
                # Parse transport layer
                if TCP in packet:
                    packet_data.update(self._parse_tcp(packet[TCP]))
                elif UDP in packet:
                    packet_data.update(self._parse_udp(packet[UDP]))
                elif ICMP in packet:
                    packet_data.update(self._parse_icmp(packet[ICMP]))
            
            # Parse IPv6
            elif IPv6 in packet:
                ipv6_layer = packet[IPv6]
                packet_data.update({
                    'src_ip': ipv6_layer.src,
                    'dst_ip': ipv6_layer.dst,
                    'protocol': 'IPv6',
                    'ttl': ipv6_layer.hlim
                })
            
            # Parse ARP
            elif ARP in packet:
                packet_data.update(self._parse_arp(packet[ARP]))
            
            # Generate payload hash for analysis
            if Raw in packet:
                payload = bytes(packet[Raw])
                packet_data['payload_hash'] = hashlib.md5(payload).hexdigest()[:16]
            
            # Create and return PacketModel
            if 'src_ip' in packet_data and 'dst_ip' in packet_data:
                return PacketModel(
                    src_ip=packet_data['src_ip'],
                    dst_ip=packet_data['dst_ip'],
                    protocol=packet_data['protocol'],
                    packet_size=packet_data['packet_size'],
                    timestamp=packet_data['timestamp'],
                    src_port=packet_data.get('src_port'),
                    dst_port=packet_data.get('dst_port'),
                    ttl=packet_data.get('ttl'),
                    flags=packet_data.get('flags'),
                    payload_hash=packet_data.get('payload_hash'),
                    window_size=packet_data.get('window_size'),
                    checksum=packet_data.get('checksum'),
                    fragment_offset=packet_data.get('fragment_offset'),
                    dns_query=packet_data.get('dns_query'),
                    http_method=packet_data.get('http_method'),
                    http_host=packet_data.get('http_host')
                )
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error parsing packet: {e}")
            return None
    
    def _parse_tcp(self, tcp_layer) -> Dict[str, Any]:
        """Parse TCP layer information"""
        flags = []
        if tcp_layer.flags & 0x01: flags.append('FIN')
        if tcp_layer.flags & 0x02: flags.append('SYN')
        if tcp_layer.flags & 0x04: flags.append('RST')
        if tcp_layer.flags & 0x08: flags.append('PSH')
        if tcp_layer.flags & 0x10: flags.append('ACK')
        if tcp_layer.flags & 0x20: flags.append('URG')
        
        return {
            'protocol': 'TCP',
            'src_port': tcp_layer.sport,
            'dst_port': tcp_layer.dport,
            'flags': '|'.join(flags),
            'window_size': tcp_layer.window,
            'seq_num': tcp_layer.seq,
            'ack_num': tcp_layer.ack
        }
    
    def _parse_udp(self, udp_layer) -> Dict[str, Any]:
        """Parse UDP layer information"""
        return {
            'protocol': 'UDP',
            'src_port': udp_layer.sport,
            'dst_port': udp_layer.dport,
            'udp_length': udp_layer.len
        }
    
    def _parse_icmp(self, icmp_layer) -> Dict[str, Any]:
        """Parse ICMP layer information"""
        return {
            'protocol': 'ICMP',
            'icmp_type': icmp_layer.type,
            'icmp_code': icmp_layer.code
        }
    
    def _parse_arp(self, arp_layer) -> Dict[str, Any]:
        """Parse ARP layer information"""
        return {
            'protocol': 'ARP',
            'src_ip': arp_layer.psrc,
            'dst_ip': arp_layer.pdst,
            'src_mac': arp_layer.hwsrc,
            'dst_mac': arp_layer.hwdst,
            'arp_op': arp_layer.op
        }
    
    def _parse_ipv6(self, ipv6_layer) -> Dict[str, Any]:
        """Parse IPv6 layer information"""
        return {
            'protocol': 'IPv6',
            'src_ip': ipv6_layer.src,
            'dst_ip': ipv6_layer.dst,
            'traffic_class': ipv6_layer.tc,
            'flow_label': ipv6_layer.fl,
            'hop_limit': ipv6_layer.hlim
        }
    
    def _stats_loop(self):
        """Background thread to calculate packet rates"""
        while self.is_capturing:
            try:
                time.sleep(1)
                if self.stats['start_time']:
                    runtime = (datetime.now() - self.stats['start_time']).total_seconds()
                    pps = self.stats['total_packets'] / max(runtime, 1)
                    self.stats['packet_rates'].append(pps)
                    
                    # Keep only last 60 seconds of rates
                    if len(self.stats['packet_rates']) > 60:
                        self.stats['packet_rates'] = self.stats['packet_rates'][-60:]
                        
            except Exception as e:
                logger.error(f"❌ Error in stats loop: {e}")
    
    def get_packet(self, timeout: float = 1.0) -> Optional[PacketModel]:
        """Get next packet from the processing queue"""
        try:
            return self.packet_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive capture statistics"""
        runtime = 0
        pps = 0
        bps = 0
        
        if self.stats['start_time']:
            runtime = (datetime.now() - self.stats['start_time']).total_seconds()
            pps = self.stats['total_packets'] / max(runtime, 1)
            bps = self.stats['bytes_captured'] / max(runtime, 1)
        
        return {
            'is_capturing': self.is_capturing,
            'interface': self.interface,
            'total_packets': self.stats['total_packets'],
            'dropped_packets': self.stats['dropped_packets'],
            'bytes_captured': self.stats['bytes_captured'],
            'runtime_seconds': runtime,
            'packets_per_second': round(pps, 2),
            'bytes_per_second': round(bps, 2),
            'mbps': round((bps * 8) / (1024 * 1024), 3),
            'queue_size': self.packet_queue.qsize(),
            'buffer_utilization': round((self.packet_queue.qsize() / self.buffer_size) * 100, 1),
            'protocol_distribution': dict(self.stats['protocols']),
            'error_count': self.stats['errors'],
            'recent_packet_rates': self.stats['packet_rates'][-10:] if self.stats['packet_rates'] else []
        }
    
    def get_interface_info(self) -> Dict[str, Any]:
        """Get detailed information about the capture interface"""
        try:
            net_stats = psutil.net_if_stats()
            net_addrs = psutil.net_if_addrs()
            
            if self.interface in net_stats:
                stats = net_stats[self.interface]
                info = {
                    'name': self.interface,
                    'is_up': stats.isup,
                    'speed': stats.speed,
                    'mtu': stats.mtu,
                    'addresses': []
                }
                
                if self.interface in net_addrs:
                    for addr in net_addrs[self.interface]:
                        info['addresses'].append({
                            'family': addr.family.name,
                            'address': addr.address,
                            'netmask': addr.netmask,
                            'broadcast': addr.broadcast
                        })
                
                return info
            else:
                return {'name': self.interface, 'error': 'Interface not found'}
                
        except Exception as e:
            logger.error(f"❌ Error getting interface info: {e}")
            return {'name': self.interface, 'error': str(e)}

# Example usage and testing
if __name__ == "__main__":
    def test_packet_callback(packet: PacketModel):
        """Test callback function"""
        print(f"📦 {packet.src_ip} → {packet.dst_ip} ({packet.protocol}) - {packet.packet_size} bytes")
    
    # Create capture engine
    capture = PacketCaptureEngine()
    capture.add_callback(test_packet_callback)
    
    print("🔍 Available interfaces:")
    interface_info = capture.get_interface_info()
    print(json.dumps(interface_info, indent=2))
    
    # Start capture
    print("\n🚀 Starting packet capture for 30 seconds...")
    if capture.start_capture():
        try:
            time.sleep(30)
        except KeyboardInterrupt:
            print("\n🛑 Interrupted by user")
        finally:
            capture.stop_capture()
            
            # Print final statistics
            stats = capture.get_statistics()
            print("\n📊 Final Statistics:")
            print(f"   Total packets: {stats['total_packets']}")
            print(f"   Dropped packets: {stats['dropped_packets']}")
            print(f"   Average PPS: {stats['packets_per_second']}")
            print(f"   Data rate: {stats['mbps']} Mbps")
            print(f"   Protocol breakdown: {stats['protocol_distribution']}")
    else:
        print("❌ Failed to start packet capture")