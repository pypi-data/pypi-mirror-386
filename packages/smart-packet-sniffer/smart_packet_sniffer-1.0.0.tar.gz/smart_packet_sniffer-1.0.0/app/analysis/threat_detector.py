"""
Advanced Threat Detection System
Multi-layered security analysis using signature-based, ML-based, and behavioral detection
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from collections import defaultdict, Counter, deque
from datetime import datetime, timedelta
import threading
import time
import logging
import json
import re
from typing import Dict, List, Optional, Any, Tuple
import pickle

from app.models.packet_model import PacketModel, ThreatModel

logger = logging.getLogger(__name__)

class ThreatDetector:
    """Advanced multi-layered threat detection system"""
    
    def __init__(self):
        self.signature_detector = SignatureBasedDetector()
        self.anomaly_detector = AnomalyDetector()
        self.behavioral_detector = BehaviorAnalyzer()
        self.threat_correlator = ThreatCorrelator()
        
        # Detection statistics
        self.detection_stats = {
            'total_analyzed': 0,
            'threats_detected': 0,
            'false_positives': 0,
            'detection_rates': defaultdict(int),
            'severity_counts': defaultdict(int)
        }
        
        # Thread safety
        self.lock = threading.RLock()
        
        # Known threat intelligence (simplified)
        self.threat_intelligence = self._load_threat_intelligence()
        
        logger.info("🛡️ Advanced threat detection system initialized")
    
    def analyze_packet(self, packet: PacketModel) -> List[ThreatModel]:
        """Main threat analysis entry point"""
        with self.lock:
            self.detection_stats['total_analyzed'] += 1
        
        all_threats = []
        
        try:
            # Layer 1: Signature-based detection
            signature_threats = self.signature_detector.detect(packet)
            all_threats.extend(signature_threats)
            
            # Layer 2: Machine learning anomaly detection
            anomaly_threats = self.anomaly_detector.detect(packet)
            all_threats.extend(anomaly_threats)
            
            # Layer 3: Behavioral analysis
            behavioral_threats = self.behavioral_detector.analyze(packet)
            all_threats.extend(behavioral_threats)
            
            # Layer 4: Threat correlation and enrichment
            if all_threats:
                all_threats = self.threat_correlator.correlate_threats(all_threats, packet)
            
            # Update statistics
            if all_threats:
                with self.lock:
                    self.detection_stats['threats_detected'] += 1
                    for threat in all_threats:
                        self.detection_stats['detection_rates'][threat.threat_type] += 1
                        self.detection_stats['severity_counts'][threat.severity] += 1
            
            # Enrich with threat intelligence
            enriched_threats = self._enrich_with_intelligence(all_threats, packet)
            
            return enriched_threats
            
        except Exception as e:
            logger.error(f"Error in threat analysis: {e}")
            return []
    
    def _load_threat_intelligence(self) -> Dict[str, Any]:
        """Load threat intelligence data"""
        # This is a simplified threat intel database
        # In production, this would integrate with real threat feeds
        return {
            'malicious_ips': {
                '10.0.0.100': {'type': 'scanner', 'confidence': 0.8},
                '192.168.100.50': {'type': 'malware_c2', 'confidence': 0.95}
            },
            'suspicious_domains': {
                'malware-domain.com': {'type': 'malware', 'confidence': 0.9},
                'phishing-site.net': {'type': 'phishing', 'confidence': 0.85}
            },
            'attack_patterns': [
                {'pattern': r'\.\./', 'type': 'directory_traversal'},
                {'pattern': r'<script.*?>', 'type': 'xss_attempt'},
                {'pattern': r'union.*select', 'type': 'sql_injection'}
            ]
        }
    
    def _enrich_with_intelligence(self, threats: List[ThreatModel], packet: PacketModel) -> List[ThreatModel]:
        """Enrich threats with threat intelligence"""
        enriched_threats = []
        
        for threat in threats:
            # Check if source IP is in threat intelligence
            if packet.src_ip in self.threat_intelligence['malicious_ips']:
                intel = self.threat_intelligence['malicious_ips'][packet.src_ip]
                threat.confidence = min(1.0, threat.confidence + 0.2)
                threat.description += f" [ThreatIntel: {intel['type']}]"
                if threat.severity in ['Low', 'Medium']:
                    threat.severity = 'High'
            
            enriched_threats.append(threat)
        
        return enriched_threats
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get detection statistics"""
        with self.lock:
            stats = self.detection_stats.copy()
        
        if stats['total_analyzed'] > 0:
            stats['detection_rate'] = round((stats['threats_detected'] / stats['total_analyzed']) * 100, 2)
        else:
            stats['detection_rate'] = 0
        
        stats['detection_rates'] = dict(stats['detection_rates'])
        stats['severity_counts'] = dict(stats['severity_counts'])
        
        return stats

class SignatureBasedDetector:
    """Rule-based threat detection using predefined signatures"""
    
    def __init__(self):
        self.detection_rules = {
            'port_scan': {
                'ports_threshold': 5,
                'time_window': 60,
                'description': 'Port scanning activity detected'
            },
            'brute_force': {
                'attempts_threshold': 10,
                'time_window': 300,
                'description': 'Brute force login attempt detected'
            },
            'ddos': {
                'packets_threshold': 1000,
                'time_window': 60,
                'description': 'DDoS attack pattern detected'
            }
        }
        
        # Track connection attempts for stateful detection
        self.connection_tracker = defaultdict(lambda: deque(maxlen=1000))
        self.login_attempts = defaultdict(lambda: deque(maxlen=100))
        self.packet_counts = defaultdict(lambda: deque(maxlen=10000))
        
        # Known attack ports
        self.attack_ports = {
            22: 'SSH', 23: 'Telnet', 135: 'RPC', 139: 'NetBIOS',
            445: 'SMB', 1433: 'MSSQL', 3389: 'RDP', 5432: 'PostgreSQL'
        }
        
        logger.info("🔍 Signature-based detector initialized")
    
    def detect(self, packet: PacketModel) -> List[ThreatModel]:
        """Detect threats using signature-based rules"""
        threats = []
        current_time = datetime.now()
        
        # Port scan detection
        port_scan_threat = self._detect_port_scan(packet, current_time)
        if port_scan_threat:
            threats.append(port_scan_threat)
        
        # Brute force detection
        brute_force_threat = self._detect_brute_force(packet, current_time)
        if brute_force_threat:
            threats.append(brute_force_threat)
        
        # DDoS detection
        ddos_threat = self._detect_ddos(packet, current_time)
        if ddos_threat:
            threats.append(ddos_threat)
        
        # Suspicious port access
        suspicious_port_threat = self._detect_suspicious_port_access(packet)
        if suspicious_port_threat:
            threats.append(suspicious_port_threat)
        
        # Protocol violations
        protocol_violation = self._detect_protocol_violations(packet)
        if protocol_violation:
            threats.append(protocol_violation)
        
        return threats
    
    def _detect_port_scan(self, packet: PacketModel, current_time: datetime) -> Optional[ThreatModel]:
        """Detect port scanning behavior"""
        src_ip = packet.src_ip
        dst_port = packet.dst_port
        
        if not dst_port:
            return None
        
        # Add to connection tracker
        self.connection_tracker[src_ip].append({
            'timestamp': current_time,
            'dst_ip': packet.dst_ip,
            'dst_port': dst_port
        })
        
        # Clean old entries
        cutoff_time = current_time - timedelta(seconds=self.detection_rules['port_scan']['time_window'])
        while self.connection_tracker[src_ip] and self.connection_tracker[src_ip][0]['timestamp'] < cutoff_time:
            self.connection_tracker[src_ip].popleft()
        
        # Check for port scan pattern
        recent_connections = list(self.connection_tracker[src_ip])
        unique_ports = set(conn['dst_port'] for conn in recent_connections)
        unique_hosts = set(conn['dst_ip'] for conn in recent_connections)
        
        if len(unique_ports) >= self.detection_rules['port_scan']['ports_threshold']:
            confidence = min(1.0, len(unique_ports) / 20.0)  # Max confidence at 20 ports
            
            return ThreatModel(
                threat_type='port_scan',
                severity='High' if len(unique_ports) > 10 else 'Medium',
                description=f'Port scan from {src_ip}: {len(unique_ports)} unique ports, {len(unique_hosts)} hosts',
                confidence=confidence,
                src_ip=src_ip,
                details={
                    'unique_ports': len(unique_ports),
                    'unique_hosts': len(unique_hosts),
                    'scan_duration': self.detection_rules['port_scan']['time_window'],
                    'scan_rate': len(unique_ports) / self.detection_rules['port_scan']['time_window']
                }
            )
        
        return None
    
    def _detect_brute_force(self, packet: PacketModel, current_time: datetime) -> Optional[ThreatModel]:
        """Detect brute force login attempts"""
        # Focus on common authentication ports
        auth_ports = [22, 23, 21, 25, 110, 143, 993, 995, 3389]
        
        if packet.dst_port not in auth_ports:
            return None
        
        src_ip = packet.src_ip
        dst_combo = f"{packet.dst_ip}:{packet.dst_port}"
        
        # Track login attempts
        self.login_attempts[f"{src_ip}->{dst_combo}"].append(current_time)
        
        # Clean old attempts
        cutoff_time = current_time - timedelta(seconds=self.detection_rules['brute_force']['time_window'])
        recent_attempts = [
            attempt for attempt in self.login_attempts[f"{src_ip}->{dst_combo}"]
            if attempt > cutoff_time
        ]
        self.login_attempts[f"{src_ip}->{dst_combo}"] = deque(recent_attempts, maxlen=100)
        
        # Check threshold
        if len(recent_attempts) >= self.detection_rules['brute_force']['attempts_threshold']:
            service = self.attack_ports.get(packet.dst_port, f"port {packet.dst_port}")
            
            return ThreatModel(
                threat_type='brute_force',
                severity='High',
                description=f'Brute force attack on {service} from {src_ip} to {packet.dst_ip}',
                confidence=min(1.0, len(recent_attempts) / 50.0),
                src_ip=src_ip,
                dst_ip=packet.dst_ip,
                details={
                    'attempts_count': len(recent_attempts),
                    'target_service': service,
                    'attack_duration': self.detection_rules['brute_force']['time_window'],
                    'attempt_rate': len(recent_attempts) / self.detection_rules['brute_force']['time_window']
                }
            )
        
        return None
    
    def _detect_ddos(self, packet: PacketModel, current_time: datetime) -> Optional[ThreatModel]:
        """Detect DDoS attack patterns"""
        src_ip = packet.src_ip
        
        # Track packet count per source
        self.packet_counts[src_ip].append(current_time)
        
        # Clean old packets
        cutoff_time = current_time - timedelta(seconds=self.detection_rules['ddos']['time_window'])
        recent_packets = [pkt_time for pkt_time in self.packet_counts[src_ip] if pkt_time > cutoff_time]
        self.packet_counts[src_ip] = deque(recent_packets, maxlen=10000)
        
        # Check for high packet rate
        if len(recent_packets) >= self.detection_rules['ddos']['packets_threshold']:
            packet_rate = len(recent_packets) / self.detection_rules['ddos']['time_window']
            
            return ThreatModel(
                threat_type='ddos_attempt',
                severity='Critical',
                description=f'DDoS attack detected from {src_ip}: {len(recent_packets)} packets in {self.detection_rules["ddos"]["time_window"]}s',
                confidence=min(1.0, packet_rate / 2000),  # Max confidence at 2000 pps
                src_ip=src_ip,
                dst_ip=packet.dst_ip,
                details={
                    'packet_count': len(recent_packets),
                    'packets_per_second': packet_rate,
                    'attack_window': self.detection_rules['ddos']['time_window'],
                    'target_ip': packet.dst_ip
                }
            )
        
        return None
    
    def _detect_suspicious_port_access(self, packet: PacketModel) -> Optional[ThreatModel]:
        """Detect access to commonly attacked ports"""
        if packet.dst_port in self.attack_ports:
            service = self.attack_ports[packet.dst_port]
            
            return ThreatModel(
                threat_type='suspicious_port_access',
                severity='Medium',
                description=f'Access to {service} service (port {packet.dst_port}) from {packet.src_ip}',
                confidence=0.6,  # Medium confidence for port access
                src_ip=packet.src_ip,
                dst_ip=packet.dst_ip,
                details={
                    'target_port': packet.dst_port,
                    'target_service': service,
                    'protocol': packet.protocol
                }
            )
        
        return None
    
    def _detect_protocol_violations(self, packet: PacketModel) -> Optional[ThreatModel]:
        """Detect protocol violations and malformed packets"""
        violations = []
        
        # Check for suspicious packet sizes
        if packet.packet_size > 65535:  # Maximum IP packet size
            violations.append("Oversized packet")
        elif packet.packet_size < 20:  # Minimum IP header
            violations.append("Undersized packet")
        
        # Check for suspicious TTL values
        if packet.ttl and (packet.ttl > 255 or packet.ttl < 1):
            violations.append("Invalid TTL value")
        
        # Check for suspicious port combinations
        if (packet.src_port and packet.dst_port and 
            packet.src_port == packet.dst_port and 
            packet.src_port < 1024):
            violations.append("Suspicious port mirroring")
        
        if violations:
            return ThreatModel(
                threat_type='protocol_violation',
                severity='Medium',
                description=f'Protocol violations detected: {", ".join(violations)}',
                confidence=0.7,
                src_ip=packet.src_ip,
                dst_ip=packet.dst_ip,
                details={
                    'violations': violations,
                    'packet_size': packet.packet_size,
                    'ttl': packet.ttl,
                    'protocol': packet.protocol
                }
            )
        
        return None

class AnomalyDetector:
    """Machine learning-based anomaly detection"""
    
    def __init__(self):
        self.model = IsolationForest(contamination=0.1, random_state=42, n_estimators=100)
        self.scaler = StandardScaler()
        self.is_trained = False
        self.training_data = []
        self.feature_buffer = deque(maxlen=10000)
        
        # Feature extraction configuration
        self.feature_columns = [
            'packet_size', 'src_port', 'dst_port', 'ttl',
            'protocol_tcp', 'protocol_udp', 'protocol_icmp',
            'hour', 'minute', 'day_of_week'
        ]
        
        logger.info("🤖 ML anomaly detector initialized")
    
    def detect(self, packet: PacketModel) -> List[ThreatModel]:
        """Detect anomalies using machine learning"""
        features = self._extract_features(packet)
        self.feature_buffer.append(features)
        
        # Train model if we have enough data and model is not trained
        if len(self.feature_buffer) >= 1000 and not self.is_trained:
            self._train_model()
        
        # Perform anomaly detection if model is trained
        if self.is_trained:
            return self._detect_anomaly(packet, features)
        
        return []
    
    def _extract_features(self, packet: PacketModel) -> Dict[str, float]:
        """Extract numerical features from packet"""
        timestamp = packet.timestamp or datetime.now()
        
        features = {
            'packet_size': float(packet.packet_size),
            'src_port': float(packet.src_port or 0),
            'dst_port': float(packet.dst_port or 0),
            'ttl': float(packet.ttl or 64),
            'protocol_tcp': 1.0 if packet.protocol == 'TCP' else 0.0,
            'protocol_udp': 1.0 if packet.protocol == 'UDP' else 0.0,
            'protocol_icmp': 1.0 if packet.protocol == 'ICMP' else 0.0,
            'hour': float(timestamp.hour),
            'minute': float(timestamp.minute),
            'day_of_week': float(timestamp.weekday())
        }
        
        return features
    
    def _train_model(self):
        """Train the anomaly detection model"""
        try:
            # Convert buffer to training data
            feature_matrix = []
            for features in self.feature_buffer:
                feature_vector = [features[col] for col in self.feature_columns]
                feature_matrix.append(feature_vector)
            
            if len(feature_matrix) < 100:
                return
            
            # Scale features
            feature_array = np.array(feature_matrix)
            scaled_features = self.scaler.fit_transform(feature_array)
            
            # Train model
            self.model.fit(scaled_features)
            self.is_trained = True
            
            logger.info(f"🎯 ML model trained on {len(feature_matrix)} samples")
            
        except Exception as e:
            logger.error(f"Error training ML model: {e}")
    
    def _detect_anomaly(self, packet: PacketModel, features: Dict[str, float]) -> List[ThreatModel]:
        """Detect if packet is anomalous"""
        try:
            # Convert features to array
            feature_vector = np.array([[features[col] for col in self.feature_columns]])
            
            # Scale features
            scaled_features = self.scaler.transform(feature_vector)
            
            # Get anomaly score and prediction
            anomaly_score = self.model.decision_function(scaled_features)[0]
            is_anomaly = self.model.predict(scaled_features)[0] == -1
            
            if is_anomaly:
                # Convert score to confidence (0-1)
                confidence = min(1.0, abs(anomaly_score) / 0.5)
                severity = 'High' if confidence > 0.8 else 'Medium' if confidence > 0.5 else 'Low'
                
                return [ThreatModel(
                    threat_type='anomalous_behavior',
                    severity=severity,
                    description=f'Anomalous network behavior detected (ML confidence: {confidence:.2f})',
                    confidence=confidence,
                    src_ip=packet.src_ip,
                    dst_ip=packet.dst_ip,
                    details={
                        'anomaly_score': anomaly_score,
                        'model_type': 'IsolationForest',
                        'feature_vector': features,
                        'detection_method': 'machine_learning'
                    }
                )]
            
        except Exception as e:
            logger.error(f"Error in ML anomaly detection: {e}")
        
        return []

class BehaviorAnalyzer:
    """Behavioral analysis for advanced threat detection"""
    
    def __init__(self, time_window: int = 600):  # 10 minutes
        self.time_window = time_window
        self.host_behaviors = defaultdict(lambda: {
            'packets': deque(maxlen=10000),
            'communications': defaultdict(list),
            'ports_accessed': set(),
            'protocols_used': set(),
            'first_seen': None,
            'byte_count': 0
        })
        
        logger.info("🧠 Behavioral analyzer initialized")
    
    def analyze(self, packet: PacketModel) -> List[ThreatModel]:
        """Analyze packet for behavioral anomalies"""
        threats = []
        current_time = datetime.now()
        src_ip = packet.src_ip
        
        # Update host behavior profile
        self._update_behavior_profile(packet, current_time)
        
        # Perform behavioral analysis
        threats.extend(self._detect_data_exfiltration(src_ip, packet, current_time))
        threats.extend(self._detect_command_and_control(src_ip, packet, current_time))
        threats.extend(self._detect_lateral_movement(src_ip, packet, current_time))
        threats.extend(self._detect_reconnaissance(src_ip, packet, current_time))
        
        return threats
    
    def _update_behavior_profile(self, packet: PacketModel, timestamp: datetime):
        """Update behavioral profile for source IP"""
        src_ip = packet.src_ip
        behavior = self.host_behaviors[src_ip]
        
        # Add packet to history
        behavior['packets'].append({
            'timestamp': timestamp,
            'dst_ip': packet.dst_ip,
            'dst_port': packet.dst_port,
            'protocol': packet.protocol,
            'size': packet.packet_size
        })
        
        # Update communication patterns
        if packet.dst_ip:
            behavior['communications'][packet.dst_ip].append(timestamp)
        
        # Update port and protocol usage
        if packet.dst_port:
            behavior['ports_accessed'].add(packet.dst_port)
        behavior['protocols_used'].add(packet.protocol)
        
        # Update first seen and byte count
        if behavior['first_seen'] is None:
            behavior['first_seen'] = timestamp
        behavior['byte_count'] += packet.packet_size
        
        # Clean old data
        self._cleanup_old_behavior_data(src_ip, timestamp)
    
    def _cleanup_old_behavior_data(self, src_ip: str, current_time: datetime):
        """Remove old behavioral data outside time window"""
        cutoff_time = current_time - timedelta(seconds=self.time_window)
        behavior = self.host_behaviors[src_ip]
        
        # Clean packet history
        while behavior['packets'] and behavior['packets'][0]['timestamp'] < cutoff_time:
            behavior['packets'].popleft()
        
        # Clean communication history
        for dst_ip, timestamps in list(behavior['communications'].items()):
            recent_timestamps = [ts for ts in timestamps if ts > cutoff_time]
            if recent_timestamps:
                behavior['communications'][dst_ip] = recent_timestamps
            else:
                del behavior['communications'][dst_ip]
    
    def _detect_data_exfiltration(self, src_ip: str, packet: PacketModel, current_time: datetime) -> List[ThreatModel]:
        """Detect potential data exfiltration patterns"""
        behavior = self.host_behaviors[src_ip]
        threats = []
        
        # Check for large data transfers
        recent_bytes = sum(pkt['size'] for pkt in behavior['packets'])
        if recent_bytes > 100 * 1024 * 1024:  # 100MB threshold
            
            # Check if it's going to external IPs
            external_transfers = defaultdict(int)
            for pkt in behavior['packets']:
                if not self._is_internal_ip(pkt['dst_ip']):
                    external_transfers[pkt['dst_ip']] += pkt['size']
            
            for dst_ip, bytes_transferred in external_transfers.items():
                if bytes_transferred > 50 * 1024 * 1024:  # 50MB to single external IP
                    threats.append(ThreatModel(
                        threat_type='data_exfiltration',
                        severity='High',
                        description=f'Large data transfer detected: {bytes_transferred/(1024*1024):.1f}MB from {src_ip} to {dst_ip}',
                        confidence=0.8,
                        src_ip=src_ip,
                        dst_ip=dst_ip,
                        details={
                            'bytes_transferred': bytes_transferred,
                            'mb_transferred': bytes_transferred / (1024 * 1024),
                            'time_window_minutes': self.time_window / 60,
                            'transfer_rate_mbps': (bytes_transferred * 8) / (self.time_window * 1024 * 1024)
                        }
                    ))
        
        return threats
    
    def _detect_command_and_control(self, src_ip: str, packet: PacketModel, current_time: datetime) -> List[ThreatModel]:
        """Detect C2 communication patterns (beaconing)"""
        behavior = self.host_behaviors[src_ip]
        threats = []
        
        # Look for regular communication patterns
        for dst_ip, timestamps in behavior['communications'].items():
            if len(timestamps) < 10:  # Need enough data points
                continue
            
            # Calculate intervals between communications
            intervals = []
            for i in range(1, len(timestamps)):
                interval = (timestamps[i] - timestamps[i-1]).total_seconds()
                intervals.append(interval)
            
            if len(intervals) >= 5:
                avg_interval = sum(intervals) / len(intervals)
                
                # Check for regularity (beaconing)
                if 30 <= avg_interval <= 3600:  # Between 30 seconds and 1 hour
                    # Calculate variation
                    variance = sum((interval - avg_interval) ** 2 for interval in intervals) / len(intervals)
                    std_dev = variance ** 0.5
                    
                    # Regular if std deviation is less than 20% of mean
                    if std_dev < (avg_interval * 0.2):
                        threats.append(ThreatModel(
                            threat_type='c2_beaconing',
                            severity='High',
                            description=f'Regular C2 beaconing detected: {src_ip} -> {dst_ip} every {avg_interval:.0f}s',
                            confidence=0.85,
                            src_ip=src_ip,
                            dst_ip=dst_ip,
                            details={
                                'beacon_interval_seconds': avg_interval,
                                'interval_std_dev': std_dev,
                                'regularity_score': 1 - (std_dev / avg_interval),
                                'beacon_count': len(timestamps),
                                'total_duration_minutes': (timestamps[-1] - timestamps[0]).total_seconds() / 60
                            }
                        ))
        
        return threats
    
    def _detect_lateral_movement(self, src_ip: str, packet: PacketModel, current_time: datetime) -> List[ThreatModel]:
        """Detect lateral movement patterns"""
        behavior = self.host_behaviors[src_ip]
        threats = []
        
        # Check for connections to many internal hosts
        internal_destinations = set()
        admin_port_connections = 0
        
        for pkt in behavior['packets']:
            if self._is_internal_ip(pkt['dst_ip']):
                internal_destinations.add(pkt['dst_ip'])
                
                # Count connections to administrative ports
                if pkt['dst_port'] in [22, 23, 135, 139, 445, 3389, 5985, 5986]:
                    admin_port_connections += 1
        
        # Detect lateral movement if connecting to many internal hosts with admin ports
        if len(internal_destinations) > 5 and admin_port_connections > 10:
            threats.append(ThreatModel(
                threat_type='lateral_movement',
                severity='High',
                description=f'Lateral movement detected: {src_ip} connecting to {len(internal_destinations)} internal hosts with administrative access',
                confidence=0.8,
                src_ip=src_ip,
                details={
                    'internal_hosts_contacted': len(internal_destinations),
                    'admin_port_connections': admin_port_connections,
                    'time_window_minutes': self.time_window / 60,
                    'administrative_ports': [22, 23, 135, 139, 445, 3389, 5985, 5986]
                }
            ))
        
        return threats
    
    def _detect_reconnaissance(self, src_ip: str, packet: PacketModel, current_time: datetime) -> List[ThreatModel]:
        """Detect reconnaissance activities"""
        behavior = self.host_behaviors[src_ip]
        threats = []
        
        # Check for reconnaissance patterns
        unique_ports = len(behavior['ports_accessed'])
        unique_destinations = len(behavior['communications'])
        total_packets = len(behavior['packets'])
        
        # Network scanning detection
        if unique_ports > 20 and unique_destinations > 10:
            scan_intensity = (unique_ports * unique_destinations) / max(total_packets, 1)
            
            threats.append(ThreatModel(
                threat_type='network_reconnaissance',
                severity='Medium',
                description=f'Network reconnaissance from {src_ip}: {unique_ports} ports, {unique_destinations} hosts',
                confidence=min(1.0, scan_intensity * 10),
                src_ip=src_ip,
                details={
                    'unique_ports_accessed': unique_ports,
                    'unique_destinations': unique_destinations,
                    'total_packets': total_packets,
                    'scan_intensity': scan_intensity,
                    'reconnaissance_duration': self.time_window / 60
                }
            ))
        
        return threats
    
    def _is_internal_ip(self, ip: str) -> bool:
        """Check if IP address is internal/private"""
        if not ip:
            return False
        
        try:
            parts = ip.split('.')
            if len(parts) != 4:
                return False
            
            parts = [int(part) for part in parts]
            
            # Private IP ranges
            return (
                (parts[0] == 10) or  # 10.0.0.0/8
                (parts[0] == 172 and 16 <= parts[1] <= 31) or  # 172.16.0.0/12
                (parts[0] == 192 and parts[1] == 168) or  # 192.168.0.0/16
                (parts[0] == 127)  # Loopback
            )
        except ValueError:
            return False

class ThreatCorrelator:
    """Correlates and enriches threat detections"""
    
    def __init__(self):
        self.correlation_rules = {
            'escalating_attack': {
                'threats': ['port_scan', 'brute_force'],
                'time_window': 600,  # 10 minutes
                'description': 'Multi-stage attack detected'
            },
            'apt_indicators': {
                'threats': ['c2_beaconing', 'lateral_movement', 'data_exfiltration'],
                'time_window': 3600,  # 1 hour
                'description': 'Advanced Persistent Threat indicators'
            }
        }
        
        # Store recent threats for correlation
        self.recent_threats = deque(maxlen=1000)
        
    def correlate_threats(self, new_threats: List[ThreatModel], packet: PacketModel) -> List[ThreatModel]:
        """Correlate new threats with recent threats"""
        current_time = datetime.now()
        
        # Add new threats to history
        for threat in new_threats:
            self.recent_threats.append({
                'threat': threat,
                'timestamp': current_time,
                'src_ip': packet.src_ip
            })
        
        # Check for correlation patterns
        correlated_threats = self._check_correlations(packet.src_ip, current_time)
        
        # Combine original threats with correlated ones
        all_threats = new_threats + correlated_threats
        
        # Clean old threat history
        self._cleanup_old_threats(current_time)
        
        return all_threats
    
    def _check_correlations(self, src_ip: str, current_time: datetime) -> List[ThreatModel]:
        """Check for threat correlation patterns"""
        correlated_threats = []
        
        for rule_name, rule in self.correlation_rules.items():
            cutoff_time = current_time - timedelta(seconds=rule['time_window'])
            
            # Get recent threats from this source
            recent_src_threats = [
                entry['threat'] for entry in self.recent_threats
                if entry['src_ip'] == src_ip and entry['timestamp'] > cutoff_time
            ]
            
            # Check if we have the required threat types
            threat_types_seen = set(threat.threat_type for threat in recent_src_threats)
            required_types = set(rule['threats'])
            
            if required_types.issubset(threat_types_seen):
                # Create correlated threat
                correlated_threats.append(ThreatModel(
                    threat_type=rule_name,
                    severity='Critical',
                    description=f"{rule['description']} from {src_ip}",
                    confidence=0.9,
                    src_ip=src_ip,
                    details={
                        'correlated_threats': list(threat_types_seen),
                        'correlation_window_minutes': rule['time_window'] / 60,
                        'threat_count': len(recent_src_threats)
                    }
                ))
        
        return correlated_threats
    
    def _cleanup_old_threats(self, current_time: datetime):
        """Remove old threats from correlation history"""
        # Keep threats from last 2 hours for correlation
        cutoff_time = current_time - timedelta(hours=2)
        
        while self.recent_threats and self.recent_threats[0]['timestamp'] < cutoff_time:
            self.recent_threats.popleft()

# Test the threat detection system
if __name__ == "__main__":
    detector = ThreatDetector()
    
    # Create test packets that should trigger detections
    test_packets = [
        # Port scan simulation
        PacketModel(
            src_ip='192.168.1.100', dst_ip='8.8.8.8', dst_port=22,
            protocol='TCP', packet_size=64
        ),
        PacketModel(
            src_ip='192.168.1.100', dst_ip='8.8.8.8', dst_port=23,
            protocol='TCP', packet_size=64
        ),
        PacketModel(
            src_ip='192.168.1.100', dst_ip='8.8.8.8', dst_port=80,
            protocol='TCP', packet_size=64
        ),
        PacketModel(
            src_ip='192.168.1.100', dst_ip='8.8.8.8', dst_port=443,
            protocol='TCP', packet_size=64
        ),
        PacketModel(
            src_ip='192.168.1.100', dst_ip='8.8.8.8', dst_port=445,
            protocol='TCP', packet_size=64
        ),
        PacketModel(
            src_ip='192.168.1.100', dst_ip='8.8.8.8', dst_port=3389,
            protocol='TCP', packet_size=64
        ),
    ]
    
    threats_detected = 0
    for packet in test_packets:
        threats = detector.analyze_packet(packet)
        threats_detected += len(threats)
        for threat in threats:
            print(f"🚨 {threat.threat_type}: {threat.description}")
    
    # Print statistics
    stats = detector.get_statistics()
    print(f"\n📊 Detection Statistics:")
    print(f"   Total analyzed: {stats['total_analyzed']}")
    print(f"   Threats detected: {stats['threats_detected']}")
    print(f"   Detection rate: {stats['detection_rate']}%")
    print(f"   Threat types: {stats['detection_rates']}")
    
    print("✅ Threat detection system test completed!")
