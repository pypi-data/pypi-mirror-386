"""
Advanced Traffic Analysis Module
Performs statistical analysis and pattern detection on network traffic
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

import numpy as np
import pandas as pd
from collections import defaultdict, Counter, deque
from datetime import datetime, timedelta
import threading
import time
import logging
from typing import Dict, List, Optional, Any, Tuple
from statistics import mean, median, stdev
import json

from app.models.packet_model import PacketModel

logger = logging.getLogger(__name__)

class TrafficAnalyzer:
    """Advanced traffic analysis with real-time statistics and pattern detection"""
    
    def __init__(self, analysis_window_seconds: int = 300):
        """Initialize traffic analyzer with configurable analysis window"""
        self.analysis_window = analysis_window_seconds
        self.packet_buffer = deque(maxlen=50000)  # Circular buffer for efficiency
        self.analysis_results = {}
        self.buffer_lock = threading.RLock()
        self.is_analyzing = False
        
        # Real-time statistics
        self.real_time_stats = {
            'total_packets': 0,
            'total_bytes': 0,
            'protocols': defaultdict(int),
            'top_talkers': defaultdict(int),
            'port_activity': defaultdict(int),
            'packet_sizes': deque(maxlen=1000),
            'timestamps': deque(maxlen=1000)
        }
        
        # Analysis components
        self.bandwidth_analyzer = BandwidthAnalyzer()
        self.flow_analyzer = FlowAnalyzer()
        self.pattern_detector = PatternDetector()
        
        logger.info(f"📊 Traffic analyzer initialized with {analysis_window_seconds}s window")
    
    def add_packet(self, packet: PacketModel):
        """Add packet to analysis buffer with real-time processing"""
        with self.buffer_lock:
            current_time = datetime.now()
            
            # Add timestamp for time-based analysis
            enhanced_packet = {
                'packet': packet,
                'analysis_timestamp': current_time,
                'hour': current_time.hour,
                'minute': current_time.minute,
                'day_of_week': current_time.weekday()
            }
            
            self.packet_buffer.append(enhanced_packet)
            
            # Update real-time statistics
            self._update_real_time_stats(packet, current_time)
            
            # Trigger analysis if buffer is getting full
            if len(self.packet_buffer) % 1000 == 0:
                self._cleanup_old_packets(current_time)
    
    def _update_real_time_stats(self, packet: PacketModel, timestamp: datetime):
        """Update real-time statistics for immediate dashboard display"""
        self.real_time_stats['total_packets'] += 1
        self.real_time_stats['total_bytes'] += packet.packet_size
        self.real_time_stats['protocols'][packet.protocol] += 1
        self.real_time_stats['top_talkers'][packet.src_ip] += 1
        
        if packet.dst_port:
            self.real_time_stats['port_activity'][packet.dst_port] += 1
        
        self.real_time_stats['packet_sizes'].append(packet.packet_size)
        self.real_time_stats['timestamps'].append(timestamp)
    
    def _cleanup_old_packets(self, current_time: datetime):
        """Remove packets older than analysis window"""
        cutoff_time = current_time - timedelta(seconds=self.analysis_window)
        
        while self.packet_buffer and self.packet_buffer[0]['analysis_timestamp'] < cutoff_time:
            self.packet_buffer.popleft()
    
    def start_analysis(self):
        """Start continuous analysis in background thread"""
        if self.is_analyzing:
            return False
        
        self.is_analyzing = True
        analysis_thread = threading.Thread(target=self._analysis_loop, daemon=True)
        analysis_thread.start()
        
        logger.info("🔄 Traffic analysis started")
        return True
    
    def stop_analysis(self):
        """Stop traffic analysis"""
        self.is_analyzing = False
        logger.info("⏹️ Traffic analysis stopped")
    
    def _analysis_loop(self):
        """Main analysis loop running in background"""
        while self.is_analyzing:
            try:
                self._perform_comprehensive_analysis()
                time.sleep(30)  # Analyze every 30 seconds
            except Exception as e:
                logger.error(f"Error in analysis loop: {e}")
    
    def _perform_comprehensive_analysis(self):
        """Perform comprehensive traffic analysis"""
        with self.buffer_lock:
            if not self.packet_buffer:
                return
            
            packets_list = list(self.packet_buffer)
        
        analysis_timestamp = datetime.now()
        
        try:
            # Comprehensive analysis components
            basic_stats = self._calculate_advanced_statistics(packets_list)
            protocol_analysis = self._analyze_protocol_behavior(packets_list)
            communication_analysis = self._analyze_communication_patterns(packets_list)
            temporal_analysis = self._analyze_temporal_patterns(packets_list)
            bandwidth_analysis = self.bandwidth_analyzer.analyze(packets_list)
            flow_analysis = self.flow_analyzer.analyze(packets_list)
            pattern_analysis = self.pattern_detector.detect_patterns(packets_list)
            
            # Store comprehensive results
            self.analysis_results = {
                'timestamp': analysis_timestamp,
                'basic_statistics': basic_stats,
                'protocol_analysis': protocol_analysis,
                'communication_patterns': communication_analysis,
                'temporal_patterns': temporal_analysis,
                'bandwidth_analysis': bandwidth_analysis,
                'flow_analysis': flow_analysis,
                'pattern_analysis': pattern_analysis,
                'summary': self._generate_analysis_summary(
                    basic_stats, protocol_analysis, communication_analysis
                )
            }
            
            logger.info(f"📊 Analysis completed: {len(packets_list)} packets analyzed")
            
        except Exception as e:
            logger.error(f"Error in comprehensive analysis: {e}")
    
    def _calculate_advanced_statistics(self, packets_list: List[Dict]) -> Dict[str, Any]:
        """Calculate advanced statistical metrics"""
        if not packets_list:
            return {}
        
        packet_sizes = [p['packet']['packet_size'] for p in packets_list]
        timestamps = [p['analysis_timestamp'] for p in packets_list]
        
        # Inter-arrival time analysis
        inter_arrival_times = []
        for i in range(1, len(timestamps)):
            delta = (timestamps[i] - timestamps[i-1]).total_seconds()
            if delta > 0:
                inter_arrival_times.append(delta)
        
        # Protocol distribution with percentages
        protocol_counts = defaultdict(int)
        for p in packets_list:
            protocol_counts[p['packet']['protocol']] += 1
        
        total_packets = len(packets_list)
        protocol_distribution = {
            protocol: {
                'count': count,
                'percentage': round((count / total_packets) * 100, 2)
            }
            for protocol, count in protocol_counts.items()
        }
        
        return {
            'total_packets': total_packets,
            'total_bytes': sum(packet_sizes),
            'duration_seconds': (timestamps[-1] - timestamps[0]).total_seconds(),
            'packet_rate_pps': total_packets / max((timestamps[-1] - timestamps[0]).total_seconds(), 1),
            'packet_size_stats': {
                'min': min(packet_sizes),
                'max': max(packet_sizes),
                'mean': mean(packet_sizes),
                'median': median(packet_sizes),
                'std_dev': stdev(packet_sizes) if len(packet_sizes) > 1 else 0
            },
            'inter_arrival_stats': {
                'mean': mean(inter_arrival_times) if inter_arrival_times else 0,
                'min': min(inter_arrival_times) if inter_arrival_times else 0,
                'max': max(inter_arrival_times) if inter_arrival_times else 0,
                'std_dev': stdev(inter_arrival_times) if len(inter_arrival_times) > 1 else 0
            },
            'protocol_distribution': protocol_distribution,
            'unique_sources': len(set(p['packet']['src_ip'] for p in packets_list)),
            'unique_destinations': len(set(p['packet']['dst_ip'] for p in packets_list))
        }
    
    def _analyze_protocol_behavior(self, packets_list: List[Dict]) -> Dict[str, Any]:
        """Analyze behavior patterns for each protocol"""
        protocol_stats = defaultdict(lambda: {
            'packets': 0,
            'bytes': 0,
            'unique_sources': set(),
            'unique_destinations': set(),
            'ports': defaultdict(int),
            'packet_sizes': [],
            'flows': defaultdict(int)
        })
        
        for p in packets_list:
            packet = p['packet']
            protocol = packet.protocol
            
            protocol_stats[protocol]['packets'] += 1
            protocol_stats[protocol]['bytes'] += packet.packet_size
            protocol_stats[protocol]['unique_sources'].add(packet.src_ip)
            protocol_stats[protocol]['unique_destinations'].add(packet.dst_ip)
            protocol_stats[protocol]['packet_sizes'].append(packet.packet_size)
            
            if packet.dst_port:
                protocol_stats[protocol]['ports'][packet.dst_port] += 1
            
            # Create flow identifier
            flow_id = f"{packet.src_ip}:{packet.src_port}->{packet.dst_ip}:{packet.dst_port}"
            protocol_stats[protocol]['flows'][flow_id] += 1
        
        # Convert to serializable format with analysis
        result = {}
        for protocol, stats in protocol_stats.items():
            result[protocol] = {
                'packet_count': stats['packets'],
                'byte_count': stats['bytes'],
                'unique_sources': len(stats['unique_sources']),
                'unique_destinations': len(stats['unique_destinations']),
                'avg_packet_size': mean(stats['packet_sizes']) if stats['packet_sizes'] else 0,
                'top_ports': dict(Counter(stats['ports']).most_common(10)),
                'top_flows': dict(Counter(stats['flows']).most_common(5)),
                'flow_count': len(stats['flows'])
            }
        
        return result
    
    def _analyze_communication_patterns(self, packets_list: List[Dict]) -> Dict[str, Any]:
        """Analyze communication patterns between hosts"""
        communications = defaultdict(lambda: {
            'packet_count': 0,
            'byte_count': 0,
            'protocols': set(),
            'ports': set(),
            'first_seen': None,
            'last_seen': None,
            'directions': defaultdict(int)  # Track bidirectional communication
        })
        
        for p in packets_list:
            packet = p['packet']
            timestamp = p['analysis_timestamp']
            
            # Create communication pair (bidirectional)
            hosts = tuple(sorted([packet.src_ip, packet.dst_ip]))
            comm_key = f"{hosts[0]}<->{hosts[1]}"
            
            comm = communications[comm_key]
            comm['packet_count'] += 1
            comm['byte_count'] += packet.packet_size
            comm['protocols'].add(packet.protocol)
            
            if packet.dst_port:
                comm['ports'].add(packet.dst_port)
            if packet.src_port:
                comm['ports'].add(packet.src_port)
            
            if comm['first_seen'] is None or timestamp < comm['first_seen']:
                comm['first_seen'] = timestamp
            if comm['last_seen'] is None or timestamp > comm['last_seen']:
                comm['last_seen'] = timestamp
            
            # Track direction
            direction = f"{packet.src_ip}->{packet.dst_ip}"
            comm['directions'][direction] += 1
        
        # Convert to analysis results
        result = []
        for comm_key, stats in communications.items():
            duration = 0
            if stats['first_seen'] and stats['last_seen']:
                duration = (stats['last_seen'] - stats['first_seen']).total_seconds()
            
            # Determine if communication is bidirectional
            directions = list(stats['directions'].keys())
            is_bidirectional = len(directions) > 1
            
            result.append({
                'communication_pair': comm_key,
                'packet_count': stats['packet_count'],
                'byte_count': stats['byte_count'],
                'protocols': list(stats['protocols']),
                'ports_used': list(stats['ports']),
                'duration_seconds': duration,
                'packets_per_second': stats['packet_count'] / max(duration, 1),
                'is_bidirectional': is_bidirectional,
                'direction_balance': dict(stats['directions']),
                'communication_intensity': 'High' if stats['packet_count'] > 100 else 'Medium' if stats['packet_count'] > 10 else 'Low'
            })
        
        # Sort by packet count and return top communications
        result.sort(key=lambda x: x['packet_count'], reverse=True)
        return result[:20]
    
    def _analyze_temporal_patterns(self, packets_list: List[Dict]) -> Dict[str, Any]:
        """Analyze temporal patterns in traffic"""
        if not packets_list:
            return {}
        
        # Time-based distributions
        hourly_dist = defaultdict(int)
        minute_dist = defaultdict(int)
        weekday_dist = defaultdict(int)
        
        # Traffic bursts and patterns
        timestamps = []
        packet_rates = []
        
        for p in packets_list:
            timestamp = p['analysis_timestamp']
            timestamps.append(timestamp)
            hourly_dist[p['hour']] += 1
            minute_dist[p['minute']] += 1
            weekday_dist[p['day_of_week']] += 1
        
        # Calculate packet rates in 10-second windows
        if len(timestamps) > 1:
            start_time = timestamps[0]
            end_time = timestamps[-1]
            total_duration = (end_time - start_time).total_seconds()
            
            if total_duration > 0:
                window_size = 10  # 10-second windows
                num_windows = int(total_duration / window_size) + 1
                
                for i in range(num_windows):
                    window_start = start_time + timedelta(seconds=i * window_size)
                    window_end = window_start + timedelta(seconds=window_size)
                    
                    packets_in_window = sum(1 for ts in timestamps if window_start <= ts < window_end)
                    packet_rates.append(packets_in_window / window_size)
        
        # Detect bursts (periods of high activity)
        bursts = self._detect_traffic_bursts(packet_rates)
        
        return {
            'hourly_distribution': dict(hourly_dist),
            'minute_distribution': dict(minute_dist),
            'weekday_distribution': dict(weekday_dist),
            'packet_rate_analysis': {
                'mean_pps': mean(packet_rates) if packet_rates else 0,
                'max_pps': max(packet_rates) if packet_rates else 0,
                'min_pps': min(packet_rates) if packet_rates else 0,
                'std_dev_pps': stdev(packet_rates) if len(packet_rates) > 1 else 0
            },
            'traffic_bursts': bursts,
            'total_analysis_duration': (timestamps[-1] - timestamps[0]).total_seconds() if len(timestamps) > 1 else 0
        }
    
    def _detect_traffic_bursts(self, packet_rates: List[float]) -> List[Dict[str, Any]]:
        """Detect traffic bursts using statistical analysis"""
        if len(packet_rates) < 10:
            return []
        
        bursts = []
        mean_rate = mean(packet_rates)
        std_rate = stdev(packet_rates)
        
        # Define burst threshold as mean + 2*std_dev
        burst_threshold = mean_rate + (2 * std_rate)
        
        in_burst = False
        burst_start = None
        burst_packets = 0
        
        for i, rate in enumerate(packet_rates):
            if rate > burst_threshold and not in_burst:
                # Start of burst
                in_burst = True
                burst_start = i
                burst_packets = rate
            elif rate > burst_threshold and in_burst:
                # Continuation of burst
                burst_packets += rate
            elif rate <= burst_threshold and in_burst:
                # End of burst
                in_burst = False
                burst_duration = (i - burst_start) * 10  # 10-second windows
                
                bursts.append({
                    'start_window': burst_start,
                    'end_window': i - 1,
                    'duration_seconds': burst_duration,
                    'total_packets': burst_packets,
                    'peak_rate': max(packet_rates[burst_start:i]),
                    'intensity': 'High' if burst_packets > mean_rate * 10 else 'Medium'
                })
        
        return bursts
    
    def _generate_analysis_summary(self, basic_stats: Dict, protocol_analysis: Dict, comm_patterns: List[Dict]) -> Dict[str, Any]:
        """Generate high-level analysis summary"""
        summary = {
            'overall_activity_level': 'Low',
            'dominant_protocol': 'Unknown',
            'most_active_communication': 'None',
            'notable_patterns': [],
            'recommendations': []
        }
        
        # Determine activity level
        if basic_stats.get('packet_rate_pps', 0) > 100:
            summary['overall_activity_level'] = 'High'
        elif basic_stats.get('packet_rate_pps', 0) > 10:
            summary['overall_activity_level'] = 'Medium'
        
        # Find dominant protocol
        if protocol_analysis:
            dominant = max(protocol_analysis.items(), key=lambda x: x[1]['packet_count'])
            summary['dominant_protocol'] = f"{dominant[0]} ({dominant[1]['packet_count']} packets)"
        
        # Most active communication
        if comm_patterns:
            most_active = comm_patterns[0]
            summary['most_active_communication'] = f"{most_active['communication_pair']} ({most_active['packet_count']} packets)"
        
        # Notable patterns
        if basic_stats.get('packet_rate_pps', 0) > 50:
            summary['notable_patterns'].append("High packet rate detected")
        
        if basic_stats.get('unique_sources', 0) > 100:
            summary['notable_patterns'].append("Many unique source IPs")
        
        # Recommendations
        if summary['overall_activity_level'] == 'High':
            summary['recommendations'].append("Monitor for potential DDoS or scanning activity")
        
        if len(protocol_analysis) > 5:
            summary['recommendations'].append("Diverse protocol usage - verify all are legitimate")
        
        return summary
    
    def get_real_time_statistics(self) -> Dict[str, Any]:
        """Get current real-time statistics for dashboard"""
        with self.buffer_lock:
            # Calculate recent packet rate
            recent_timestamps = list(self.real_time_stats['timestamps'])[-60:]  # Last 60 packets
            recent_rate = 0
            if len(recent_timestamps) > 1:
                time_span = (recent_timestamps[-1] - recent_timestamps[0]).total_seconds()
                recent_rate = len(recent_timestamps) / max(time_span, 1)
            
            # Get recent packet size statistics
            recent_sizes = list(self.real_time_stats['packet_sizes'])[-100:]  # Last 100 packets
            size_stats = {}
            if recent_sizes:
                size_stats = {
                    'avg': round(mean(recent_sizes), 1),
                    'min': min(recent_sizes),
                    'max': max(recent_sizes)
                }
            
            return {
                'total_packets': self.real_time_stats['total_packets'],
                'total_bytes': self.real_time_stats['total_bytes'],
                'recent_packet_rate': round(recent_rate, 2),
                'protocol_breakdown': dict(self.real_time_stats['protocols']),
                'top_source_ips': dict(Counter(self.real_time_stats['top_talkers']).most_common(5)),
                'active_ports': dict(Counter(self.real_time_stats['port_activity']).most_common(10)),
                'packet_size_stats': size_stats,
                'buffer_size': len(self.packet_buffer),
                'analysis_window_seconds': self.analysis_window
            }
    
    def get_analysis_results(self) -> Dict[str, Any]:
        """Get latest comprehensive analysis results"""
        return self.analysis_results.copy() if self.analysis_results else {}

class BandwidthAnalyzer:
    """Specialized bandwidth analysis component"""
    
    def analyze(self, packets_list: List[Dict]) -> Dict[str, Any]:
        """Analyze bandwidth utilization patterns"""
        if not packets_list:
            return {}
        
        # Group by time windows for bandwidth calculation
        time_windows = defaultdict(lambda: {'packets': 0, 'bytes': 0})
        
        for p in packets_list:
            # 30-second time windows
            timestamp = p['analysis_timestamp']
            window_key = timestamp.replace(second=(timestamp.second // 30) * 30, microsecond=0)
            
            time_windows[window_key]['packets'] += 1
            time_windows[window_key]['bytes'] += p['packet']['packet_size']
        
        # Calculate bandwidth metrics
        bandwidth_data = []
        total_bytes = 0
        
        for window_time, stats in sorted(time_windows.items()):
            bps = stats['bytes'] / 30  # bytes per second
            total_bytes += stats['bytes']
            
            bandwidth_data.append({
                'timestamp': window_time.isoformat(),
                'bytes_per_second': bps,
                'bits_per_second': bps * 8,
                'kbps': (bps * 8) / 1024,
                'mbps': (bps * 8) / (1024 * 1024),
                'packets_per_second': stats['packets'] / 30
            })
        
        # Overall bandwidth statistics
        if bandwidth_data:
            bps_values = [b['bytes_per_second'] for b in bandwidth_data]
            return {
                'timeline_data': bandwidth_data,
                'total_bytes': total_bytes,
                'total_mb': total_bytes / (1024 * 1024),
                'peak_bps': max(bps_values),
                'avg_bps': mean(bps_values),
                'peak_mbps': max(b['mbps'] for b in bandwidth_data),
                'avg_mbps': mean(b['mbps'] for b in bandwidth_data)
            }
        
        return {}

class FlowAnalyzer:
    """Network flow analysis component"""
    
    def analyze(self, packets_list: List[Dict]) -> Dict[str, Any]:
        """Analyze network flows and connections"""
        flows = defaultdict(lambda: {
            'packets_forward': 0,
            'packets_backward': 0,
            'bytes_forward': 0,
            'bytes_backward': 0,
            'first_seen': None,
            'last_seen': None,
            'protocols': set()
        })
        
        for p in packets_list:
            packet = p['packet']
            timestamp = p['analysis_timestamp']
            
            # Create flow key (5-tuple)
            flow_key = (
                packet.src_ip, packet.src_port,
                packet.dst_ip, packet.dst_port,
                packet.protocol
            )
            
            # Also create reverse flow key
            reverse_flow_key = (
                packet.dst_ip, packet.dst_port,
                packet.src_ip, packet.src_port,
                packet.protocol
            )
            
            # Determine flow direction
            if flow_key in flows:
                flow = flows[flow_key]
                flow['packets_forward'] += 1
                flow['bytes_forward'] += packet.packet_size
            elif reverse_flow_key in flows:
                flow = flows[reverse_flow_key]
                flow['packets_backward'] += 1
                flow['bytes_backward'] += packet.packet_size
            else:
                # New flow
                flow = flows[flow_key]
                flow['packets_forward'] = 1
                flow['bytes_forward'] = packet.packet_size
            
            flow['protocols'].add(packet.protocol)
            if flow['first_seen'] is None or timestamp < flow['first_seen']:
                flow['first_seen'] = timestamp
            if flow['last_seen'] is None or timestamp > flow['last_seen']:
                flow['last_seen'] = timestamp
        
        # Analyze flows
        flow_analysis = []
        for flow_key, stats in flows.items():
            src_ip, src_port, dst_ip, dst_port, protocol = flow_key
            
            total_packets = stats['packets_forward'] + stats['packets_backward']
            total_bytes = stats['bytes_forward'] + stats['bytes_backward']
            
            duration = 0
            if stats['first_seen'] and stats['last_seen']:
                duration = (stats['last_seen'] - stats['first_seen']).total_seconds()
            
            flow_analysis.append({
                'src_ip': src_ip,
                'src_port': src_port,
                'dst_ip': dst_ip,
                'dst_port': dst_port,
                'protocol': protocol,
                'total_packets': total_packets,
                'total_bytes': total_bytes,
                'duration_seconds': duration,
                'packets_per_second': total_packets / max(duration, 1),
                'bidirectional': stats['packets_backward'] > 0,
                'forward_packets': stats['packets_forward'],
                'backward_packets': stats['packets_backward']
            })
        
        # Sort by total packets
        flow_analysis.sort(key=lambda x: x['total_packets'], reverse=True)
        
        return {
            'total_flows': len(flows),
            'top_flows': flow_analysis[:20],
            'bidirectional_flows': len([f for f in flow_analysis if f['bidirectional']]),
            'flow_summary': {
                'total_flows': len(flows),
                'avg_duration': mean([f['duration_seconds'] for f in flow_analysis if f['duration_seconds'] > 0]) if flow_analysis else 0,
                'avg_packets_per_flow': mean([f['total_packets'] for f in flow_analysis]) if flow_analysis else 0
            }
        }

class PatternDetector:
    """Advanced pattern detection in network traffic"""
    
    def detect_patterns(self, packets_list: List[Dict]) -> Dict[str, Any]:
        """Detect various patterns in network traffic"""
        patterns = {
            'periodic_communications': [],
            'data_transfer_patterns': [],
            'scanning_patterns': [],
            'time_based_patterns': []
        }
        
        # Detect periodic communications
        patterns['periodic_communications'] = self._detect_periodic_communications(packets_list)
        
        # Detect large data transfers
        patterns['data_transfer_patterns'] = self._detect_data_transfers(packets_list)
        
        # Detect scanning patterns
        patterns['scanning_patterns'] = self._detect_scanning_patterns(packets_list)
        
        return patterns
    
    def _detect_periodic_communications(self, packets_list: List[Dict]) -> List[Dict[str, Any]]:
        """Detect periodic or regular communications (potential beaconing)"""
        # Group by source-destination pairs
        communications = defaultdict(list)
        
        for p in packets_list:
            packet = p['packet']
            key = f"{packet.src_ip}->{packet.dst_ip}"
            communications[key].append(p['analysis_timestamp'])
        
        periodic_comms = []
        
        for comm_key, timestamps in communications.items():
            if len(timestamps) < 5:  # Need at least 5 communications
                continue
            
            # Calculate intervals between communications
            intervals = []
            for i in range(1, len(timestamps)):
                interval = (timestamps[i] - timestamps[i-1]).total_seconds()
                intervals.append(interval)
            
            if len(intervals) > 3:
                # Check for regularity (low standard deviation)
                mean_interval = mean(intervals)
                if len(intervals) > 1:
                    interval_std = stdev(intervals)
                    
                    # Consider periodic if std dev is less than 20% of mean
                    if interval_std < (mean_interval * 0.2) and 10 <= mean_interval <= 3600:
                        periodic_comms.append({
                            'communication': comm_key,
                            'count': len(timestamps),
                            'mean_interval_seconds': round(mean_interval, 2),
                            'interval_std_dev': round(interval_std, 2),
                            'regularity_score': round(1 - (interval_std / mean_interval), 3),
                            'duration_minutes': round((timestamps[-1] - timestamps[0]).total_seconds() / 60, 1)
                        })
        
        return periodic_comms
    
    def _detect_data_transfers(self, packets_list: List[Dict]) -> List[Dict[str, Any]]:
        """Detect large data transfer patterns"""
        # Group by flows
        flows = defaultdict(lambda: {'bytes': 0, 'packets': 0, 'start_time': None, 'end_time': None})
        
        for p in packets_list:
            packet = p['packet']
            timestamp = p['analysis_timestamp']
            flow_key = f"{packet.src_ip}:{packet.src_port}->{packet.dst_ip}:{packet.dst_port}"
            
            flows[flow_key]['bytes'] += packet.packet_size
            flows[flow_key]['packets'] += 1
            
            if flows[flow_key]['start_time'] is None or timestamp < flows[flow_key]['start_time']:
                flows[flow_key]['start_time'] = timestamp
            if flows[flow_key]['end_time'] is None or timestamp > flows[flow_key]['end_time']:
                flows[flow_key]['end_time'] = timestamp
        
        large_transfers = []
        
        for flow_key, stats in flows.items():
            # Consider large if > 1MB or > 1000 packets
            if stats['bytes'] > 1024*1024 or stats['packets'] > 1000:
                duration = 0
                if stats['start_time'] and stats['end_time']:
                    duration = (stats['end_time'] - stats['start_time']).total_seconds()
                
                large_transfers.append({
                    'flow': flow_key,
                    'total_bytes': stats['bytes'],
                    'total_mb': round(stats['bytes'] / (1024*1024), 2),
                    'total_packets': stats['packets'],
                    'duration_seconds': duration,
                    'transfer_rate_mbps': round((stats['bytes'] * 8) / (duration * 1024 * 1024), 2) if duration > 0 else 0
                })
        
        # Sort by size
        large_transfers.sort(key=lambda x: x['total_bytes'], reverse=True)
        return large_transfers[:10]
    
    def _detect_scanning_patterns(self, packets_list: List[Dict]) -> List[Dict[str, Any]]:
        """Detect potential scanning patterns"""
        # Group by source IP
        source_activities = defaultdict(lambda: {'destinations': set(), 'ports': set(), 'protocols': set()})
        
        for p in packets_list:
            packet = p['packet']
            src_ip = packet.src_ip
            
            source_activities[src_ip]['destinations'].add(packet.dst_ip)
            if packet.dst_port:
                source_activities[src_ip]['ports'].add(packet.dst_port)
            source_activities[src_ip]['protocols'].add(packet.protocol)
        
        scanning_patterns = []
        
        for src_ip, activity in source_activities.items():
            # Potential port scan: many ports, few destinations
            if len(activity['ports']) > 10 and len(activity['destinations']) < 5:
                scanning_patterns.append({
                    'type': 'Port Scan',
                    'source_ip': src_ip,
                    'unique_ports': len(activity['ports']),
                    'unique_destinations': len(activity['destinations']),
                    'protocols': list(activity['protocols'])
                })
            
            # Potential host scan: many destinations, similar ports
            elif len(activity['destinations']) > 20 and len(activity['ports']) < 5:
                scanning_patterns.append({
                    'type': 'Host Scan',
                    'source_ip': src_ip,
                    'unique_destinations': len(activity['destinations']),
                    'unique_ports': len(activity['ports']),
                    'protocols': list(activity['protocols'])
                })
        
        return scanning_patterns

# Test the traffic analyzer
if __name__ == "__main__":
    from app.models.packet_model import PacketModel
    
    analyzer = TrafficAnalyzer()
    
    # Create some test packets
    test_packets = []
    for i in range(100):
        packet = PacketModel(
            src_ip=f"192.168.1.{(i % 10) + 1}",
            dst_ip=f"8.8.8.{(i % 4) + 1}",
            protocol=['TCP', 'UDP', 'ICMP'][i % 3],
            packet_size=64 + (i % 1000),
            src_port=1024 + i,
            dst_port=80 + (i % 20)
        )
        test_packets.append(packet)
        analyzer.add_packet(packet)
    
    # Start analysis
    analyzer.start_analysis()
    
    # Wait for analysis
    time.sleep(2)
    
    # Get results
    real_time_stats = analyzer.get_real_time_statistics()
    analysis_results = analyzer.get_analysis_results()
    
    print("✅ Traffic analyzer test completed!")
    print(f"📊 Real-time stats: {real_time_stats['total_packets']} packets")
    if analysis_results:
        print(f"📈 Analysis results available: {len(analysis_results)} components")
    
    analyzer.stop_analysis()
