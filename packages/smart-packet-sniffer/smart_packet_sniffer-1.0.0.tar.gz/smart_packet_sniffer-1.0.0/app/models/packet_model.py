"""
Data models for packets and threats
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
import json

@dataclass
class PacketModel:
    """Data model for network packets"""
    src_ip: str
    dst_ip: str
    protocol: str
    packet_size: int
    timestamp: Optional[datetime] = None
    src_port: Optional[int] = None
    dst_port: Optional[int] = None
    ttl: Optional[int] = None
    flags: Optional[str] = None
    payload_hash: Optional[str] = None
    window_size: Optional[int] = None
    checksum: Optional[str] = None
    fragment_offset: Optional[int] = None
    dns_query: Optional[str] = None
    http_method: Optional[str] = None
    http_host: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database insertion"""
        return {
            'src_ip': self.src_ip,
            'dst_ip': self.dst_ip,
            'src_port': self.src_port,
            'dst_port': self.dst_port,
            'protocol': self.protocol,
            'packet_size': self.packet_size,
            'timestamp': self.timestamp,
            'ttl': self.ttl,
            'flags': self.flags,
            'payload_hash': self.payload_hash,
            'window_size': self.window_size,
            'checksum': self.checksum,
            'fragment_offset': self.fragment_offset,
            'dns_query': self.dns_query,
            'http_method': self.http_method,
            'http_host': self.http_host
        }

@dataclass
class ThreatModel:
    """Data model for detected threats"""
    threat_type: str
    severity: str
    description: str
    confidence: float
    src_ip: Optional[str] = None
    dst_ip: Optional[str] = None
    packet_id: Optional[int] = None
    details: Optional[Dict[str, Any]] = None
    detected_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database insertion"""
        return {
            'type': self.threat_type,
            'severity': self.severity,
            'description': self.description,
            'confidence': self.confidence,
            'src_ip': self.src_ip,
            'dst_ip': self.dst_ip,
            'packet_id': self.packet_id,
            'details': self.details or {},
            'detected_at': self.detected_at
        }