"""
Flask Web Dashboard for Smart Packet Sniffer
Professional web interface with real-time updates via WebSocket
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import json
import threading
import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# Import our application modules
from app.models.database import DatabaseManager
from app.models.packet_model import PacketModel
from app.capture.packet_capture import PacketCaptureEngine
from app.analysis.traffic_analyzer import TrafficAnalyzer
from app.analysis.threat_detector import ThreatDetector
from config.settings import WEB_HOST, WEB_PORT, SECRET_KEY

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask application
app = Flask(__name__, 
           template_folder='../../templates',
           static_folder='../static')
app.config['SECRET_KEY'] = SECRET_KEY
app.config['JSON_SORT_KEYS'] = False

# Initialize SocketIO for real-time communication
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

class SmartPacketSnifferApp:
    """Main application class coordinating all components"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.capture_engine = PacketCaptureEngine()
        self.traffic_analyzer = TrafficAnalyzer()
        self.threat_detector = ThreatDetector()
        
        self.is_monitoring = False
        self.monitoring_thread = None
        
        # Setup packet capture callback
        self.capture_engine.add_callback(self._process_packet)
        
        # Start traffic analyzer
        self.traffic_analyzer.start_analysis()
        
        # Statistics for dashboard
        self.dashboard_stats = {
            'session_start': datetime.now(),
            'total_packets_processed': 0,
            'total_threats_detected': 0,
            'last_update': datetime.now()
        }
        
        logger.info("🚀 Smart Packet Sniffer application initialized")
    
    def _process_packet(self, packet: PacketModel):
        """Process each captured packet"""
        try:
            # Update session statistics
            self.dashboard_stats['total_packets_processed'] += 1
            self.dashboard_stats['last_update'] = datetime.now()
            
            # Store packet in database
            packet_id = self.db_manager.insert_packet(packet.to_dict())
            
            # Add to traffic analyzer
            self.traffic_analyzer.add_packet(packet)
            
            # Analyze for threats
            threats = self.threat_detector.analyze_packet(packet)
            
            # Process any detected threats
            for threat in threats:
                threat_dict = threat.to_dict()
                threat_dict['packet_id'] = packet_id
                
                # Store threat in database
                self.db_manager.insert_threat(threat_dict)
                self.dashboard_stats['total_threats_detected'] += 1
                
                # Send real-time threat alert
                self._send_threat_alert(threat, packet)
                
                logger.warning(f"🚨 Threat detected: {threat.threat_type} from {threat.src_ip}")
            
            # Send periodic packet updates (every 10th packet)
            if self.dashboard_stats['total_packets_processed'] % 10 == 0:
                self._send_packet_update(packet)
            
        except Exception as e:
            logger.error(f"Error processing packet: {e}")
    
    def _send_threat_alert(self, threat, packet: PacketModel):
        """Send real-time threat alert to dashboard"""
        try:
            alert_data = {
                'threat_type': threat.threat_type,
                'severity': threat.severity,
                'description': threat.description,
                'confidence': threat.confidence,
                'src_ip': threat.src_ip,
                'dst_ip': threat.dst_ip,
                'timestamp': datetime.now().isoformat(),
                'details': threat.details
            }
            
            socketio.emit('threat_alert', alert_data, namespace='/')
            
        except Exception as e:
            logger.error(f"Error sending threat alert: {e}")
    
    def _send_packet_update(self, packet: PacketModel):
        """Send packet update to dashboard"""
        try:
            packet_data = {
                'src_ip': packet.src_ip,
                'dst_ip': packet.dst_ip,
                'protocol': packet.protocol,
                'packet_size': packet.packet_size,
                'src_port': packet.src_port,
                'dst_port': packet.dst_port,
                'timestamp': packet.timestamp.isoformat() if packet.timestamp else datetime.now().isoformat(),
                'total_count': self.dashboard_stats['total_packets_processed']
            }
            
            socketio.emit('packet_update', packet_data, namespace='/')
            
        except Exception as e:
            logger.error(f"Error sending packet update: {e}")
    
    def start_monitoring(self) -> Dict[str, Any]:
        """Start network monitoring"""
        if self.is_monitoring:
            return {'success': False, 'message': 'Monitoring already active'}
        
        try:
            # Start packet capture
            success = self.capture_engine.start_capture()
            if not success:
                return {'success': False, 'message': 'Failed to start packet capture'}
            
            self.is_monitoring = True
            self.dashboard_stats['session_start'] = datetime.now()
            self.dashboard_stats['total_packets_processed'] = 0
            self.dashboard_stats['total_threats_detected'] = 0
            
            # Log system event
            self.db_manager.log_system_event(
                'monitoring_started',
                {'interface': self.capture_engine.interface},
                'INFO'
            )
            
            logger.info("✅ Network monitoring started")
            return {'success': True, 'message': 'Network monitoring started successfully'}
            
        except Exception as e:
            logger.error(f"Error starting monitoring: {e}")
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def stop_monitoring(self) -> Dict[str, Any]:
        """Stop network monitoring"""
        if not self.is_monitoring:
            return {'success': False, 'message': 'Monitoring not active'}
        
        try:
            # Stop packet capture
            self.capture_engine.stop_capture()
            self.is_monitoring = False
            
            # Log system event
            session_duration = (datetime.now() - self.dashboard_stats['session_start']).total_seconds()
            self.db_manager.log_system_event(
                'monitoring_stopped',
                {
                    'duration_seconds': session_duration,
                    'packets_processed': self.dashboard_stats['total_packets_processed'],
                    'threats_detected': self.dashboard_stats['total_threats_detected']
                },
                'INFO'
            )
            
            logger.info("🛑 Network monitoring stopped")
            return {'success': True, 'message': 'Network monitoring stopped successfully'}
            
        except Exception as e:
            logger.error(f"Error stopping monitoring: {e}")
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def get_dashboard_statistics(self) -> Dict[str, Any]:
        """Get comprehensive dashboard statistics"""
        try:
            # Get database statistics
            packet_stats = self.db_manager.get_packet_statistics(hours=24)
            threat_stats = self.db_manager.get_threat_statistics(hours=24)
            
            # Get capture engine statistics
            capture_stats = self.capture_engine.get_statistics()
            
            # Get traffic analyzer statistics
            traffic_stats = self.traffic_analyzer.get_real_time_statistics()
            analysis_results = self.traffic_analyzer.get_analysis_results()
            
            # Get threat detection statistics
            detection_stats = self.threat_detector.get_statistics()
            
            # Session statistics
            session_duration = (datetime.now() - self.dashboard_stats['session_start']).total_seconds()
            
            return {
                'system_status': {
                    'is_monitoring': self.is_monitoring,
                    'session_duration_seconds': session_duration,
                    'last_update': self.dashboard_stats['last_update'].isoformat(),
                    'interface': capture_stats.get('interface', 'Unknown')
                },
                'session_stats': {
                    'packets_processed': self.dashboard_stats['total_packets_processed'],
                    'threats_detected': self.dashboard_stats['total_threats_detected'],
                    'session_start': self.dashboard_stats['session_start'].isoformat()
                },
                'packet_stats': packet_stats,
                'threat_stats': threat_stats,
                'capture_stats': capture_stats,
                'traffic_stats': traffic_stats,
                'analysis_results': analysis_results,
                'detection_stats': detection_stats,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting dashboard statistics: {e}")
            return {'error': str(e)}

# Initialize the application
sniffer_app = SmartPacketSnifferApp()

# Flask Routes
@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/status')
def get_status():
    """Get current system status"""
    try:
        interface_info = sniffer_app.capture_engine.get_interface_info()
        
        return jsonify({
            'is_monitoring': sniffer_app.is_monitoring,
            'interface': interface_info,
            'uptime_seconds': (datetime.now() - sniffer_app.dashboard_stats['session_start']).total_seconds(),
            'version': '1.0.0',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/statistics')
def get_statistics():
    """Get comprehensive system statistics"""
    try:
        stats = sniffer_app.get_dashboard_statistics()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error in /api/statistics: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/start', methods=['POST'])
def start_monitoring():
    """Start network monitoring"""
    try:
        result = sniffer_app.start_monitoring()
        if result['success']:
            # Send status update to all connected clients
            socketio.emit('monitoring_started', {
                'message': 'Network monitoring started',
                'timestamp': datetime.now().isoformat()
            })
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in /api/start: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stop', methods=['POST'])
def stop_monitoring():
    """Stop network monitoring"""
    try:
        result = sniffer_app.stop_monitoring()
        if result['success']:
            # Send status update to all connected clients
            socketio.emit('monitoring_stopped', {
                'message': 'Network monitoring stopped',
                'timestamp': datetime.now().isoformat()
            })
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in /api/stop: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/threats')
def get_recent_threats():
    """Get recent threats"""
    try:
        hours = request.args.get('hours', 1, type=int)
        threat_stats = sniffer_app.db_manager.get_threat_statistics(hours=hours)
        return jsonify(threat_stats.get('recent_threats', []))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/protocols')
def get_protocol_stats():
    """Get protocol statistics"""
    try:
        hours = request.args.get('hours', 1, type=int)
        packet_stats = sniffer_app.db_manager.get_packet_statistics(hours=hours)
        return jsonify(packet_stats.get('protocol_distribution', []))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# WebSocket Events
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info("👤 Dashboard client connected")
    emit('connected', {
        'status': 'Connected to Smart Packet Sniffer',
        'server_time': datetime.now().isoformat(),
        'monitoring_status': sniffer_app.is_monitoring
    })

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info("👤 Dashboard client disconnected")

@socketio.on('request_stats')
def handle_stats_request():
    """Handle statistics request from client"""
    try:
        stats = sniffer_app.get_dashboard_statistics()
        emit('stats_update', stats)
    except Exception as e:
        logger.error(f"Error handling stats request: {e}")
        emit('error', {'message': str(e)})

# Background thread for periodic updates
def background_stats_updater():
    """Send periodic statistics updates to connected clients"""
    while True:
        try:
            if sniffer_app.is_monitoring:
                stats = sniffer_app.get_dashboard_statistics()
                socketio.emit('stats_update', stats, namespace='/')
            socketio.sleep(5)  # Update every 5 seconds
        except Exception as e:
            logger.error(f"Error in background updater: {e}")
            socketio.sleep(10)  # Wait longer on error

# Start background thread
stats_thread = socketio.start_background_task(background_stats_updater)

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    logger.info("🌐 Starting Smart Packet Sniffer Web Dashboard")
    logger.info(f"📊 Dashboard URL: http://{WEB_HOST}:{WEB_PORT}")
    socketio.run(app, debug=False, host=WEB_HOST, port=WEB_PORT)