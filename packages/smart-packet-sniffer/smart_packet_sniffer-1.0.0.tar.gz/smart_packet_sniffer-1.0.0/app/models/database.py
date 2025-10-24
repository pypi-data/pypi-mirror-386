"""
SQLite Database Manager for Smart Packet Sniffer
Handles all database operations with thread safety and optimization
"""
import sqlite3
import threading
from datetime import datetime, timedelta
from pathlib import Path
import logging
import json
from typing import Dict, List, Optional, Any

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Thread-safe database manager for packet data storage"""
    
    def __init__(self, db_path: str = 'data/network_data.db'):
        """Initialize database manager with connection pooling"""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self.lock = threading.RLock()  # Reentrant lock for nested calls
        self.connection_pool = {}  # Thread-local connections
        
        # Initialize database schema
        self._setup_database()
        logger.info(f"Database initialized at {self.db_path}")
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local database connection"""
        thread_id = threading.get_ident()
        if thread_id not in self.connection_pool:
            conn = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                timeout=30.0
            )
            conn.row_factory = sqlite3.Row  # Enable column access by name
            self.connection_pool[thread_id] = conn
        return self.connection_pool[thread_id]
    
    def _setup_database(self):
        """Create all database tables with proper indexing"""
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Enable WAL mode for better concurrent access
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA cache_size=10000")
            cursor.execute("PRAGMA temp_store=memory")
            
            # Create packets table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS packets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    src_ip TEXT NOT NULL,
                    dst_ip TEXT NOT NULL,
                    src_port INTEGER,
                    dst_port INTEGER,
                    protocol TEXT NOT NULL,
                    packet_size INTEGER NOT NULL,
                    payload_hash TEXT,
                    flags TEXT,
                    ttl INTEGER,
                    window_size INTEGER,
                    checksum TEXT,
                    fragment_offset INTEGER,
                    dns_query TEXT,
                    http_method TEXT,
                    http_host TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create threats table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS threats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    packet_id INTEGER,
                    threat_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    description TEXT,
                    src_ip TEXT,
                    dst_ip TEXT,
                    details TEXT,  -- JSON string for additional data
                    detected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    resolved BOOLEAN DEFAULT FALSE,
                    response_action TEXT,
                    FOREIGN KEY (packet_id) REFERENCES packets (id)
                )
            ''')
            
            # Create traffic_stats table for aggregated data
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS traffic_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    time_window DATETIME NOT NULL,
                    protocol TEXT NOT NULL,
                    packet_count INTEGER DEFAULT 0,
                    byte_count INTEGER DEFAULT 0,
                    unique_src_ips INTEGER DEFAULT 0,
                    unique_dst_ips INTEGER DEFAULT 0,
                    avg_packet_size REAL DEFAULT 0.0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(time_window, protocol) ON CONFLICT REPLACE
                )
            ''')
            
            # Create system_events table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    event_data TEXT,  -- JSON string
                    severity TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create performance indexes
            self._create_indexes(cursor)
            
            conn.commit()
            logger.info("Database schema created successfully")
    
    def _create_indexes(self, cursor):
        """Create indexes for better query performance"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_packets_timestamp ON packets(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_packets_src_ip ON packets(src_ip)",
            "CREATE INDEX IF NOT EXISTS idx_packets_dst_ip ON packets(dst_ip)",
            "CREATE INDEX IF NOT EXISTS idx_packets_protocol ON packets(protocol)",
            "CREATE INDEX IF NOT EXISTS idx_packets_src_dst ON packets(src_ip, dst_ip)",
            "CREATE INDEX IF NOT EXISTS idx_threats_type ON threats(threat_type)",
            "CREATE INDEX IF NOT EXISTS idx_threats_severity ON threats(severity)",
            "CREATE INDEX IF NOT EXISTS idx_threats_detected_at ON threats(detected_at)",
            "CREATE INDEX IF NOT EXISTS idx_stats_time_window ON traffic_stats(time_window)",
            "CREATE INDEX IF NOT EXISTS idx_events_type ON system_events(event_type)"
        ]
        
        for index in indexes:
            cursor.execute(index)
        
        logger.info("Database indexes created successfully")
    
    def insert_packet(self, packet_data: Dict[str, Any]) -> Optional[int]:
        """Insert packet data with validation and error handling"""
        with self.lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO packets (
                        src_ip, dst_ip, src_port, dst_port, protocol, packet_size,
                        payload_hash, flags, ttl, window_size, checksum, 
                        fragment_offset, dns_query, http_method, http_host
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    packet_data.get('src_ip'),
                    packet_data.get('dst_ip'),
                    packet_data.get('src_port'),
                    packet_data.get('dst_port'),
                    packet_data.get('protocol'),
                    packet_data.get('packet_size', 0),
                    packet_data.get('payload_hash'),
                    packet_data.get('flags'),
                    packet_data.get('ttl'),
                    packet_data.get('window_size'),
                    packet_data.get('checksum'),
                    packet_data.get('fragment_offset'),
                    packet_data.get('dns_query'),
                    packet_data.get('http_method'),
                    packet_data.get('http_host')
                ))
                
                packet_id = cursor.lastrowid
                conn.commit()
                return packet_id
                
            except sqlite3.Error as e:
                logger.error(f"Database insert error: {e}")
                return None
            except Exception as e:
                logger.error(f"Unexpected error inserting packet: {e}")
                return None
    
    def insert_threat(self, threat_data: Dict[str, Any]) -> Optional[int]:
        """Insert threat detection data"""
        with self.lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                details_json = json.dumps(threat_data.get('details', {}))
                
                cursor.execute('''
                    INSERT INTO threats (
                        packet_id, threat_type, severity, confidence, description,
                        src_ip, dst_ip, details
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    threat_data.get('packet_id'),
                    threat_data.get('type'),
                    threat_data.get('severity'),
                    threat_data.get('confidence', 1.0),
                    threat_data.get('description'),
                    threat_data.get('src_ip'),
                    threat_data.get('dst_ip'),
                    details_json
                ))
                
                threat_id = cursor.lastrowid
                conn.commit()
                return threat_id
                
            except sqlite3.Error as e:
                logger.error(f"Database threat insert error: {e}")
                return None
    
    def get_packet_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Get comprehensive packet statistics"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Total packet count
            cursor.execute("SELECT COUNT(*) FROM packets WHERE timestamp > datetime('now', '-{} hours')".format(hours))
            total_packets = cursor.fetchone()[0]
            
            # Protocol distribution
            cursor.execute('''
                SELECT protocol, COUNT(*) as count, SUM(packet_size) as total_bytes
                FROM packets 
                WHERE timestamp > datetime('now', '-{} hours')
                GROUP BY protocol
                ORDER BY count DESC
                LIMIT 10
            '''.format(hours))
            protocol_stats = [dict(row) for row in cursor.fetchall()]
            
            # Top source IPs
            cursor.execute('''
                SELECT src_ip, COUNT(*) as packet_count, SUM(packet_size) as total_bytes
                FROM packets
                WHERE timestamp > datetime('now', '-{} hours')
                GROUP BY src_ip
                ORDER BY packet_count DESC
                LIMIT 10
            '''.format(hours))
            top_sources = [dict(row) for row in cursor.fetchall()]
            
            # Top destination IPs
            cursor.execute('''
                SELECT dst_ip, COUNT(*) as packet_count, SUM(packet_size) as total_bytes
                FROM packets
                WHERE timestamp > datetime('now', '-{} hours')
                GROUP BY dst_ip
                ORDER BY packet_count DESC
                LIMIT 10
            '''.format(hours))
            top_destinations = [dict(row) for row in cursor.fetchall()]
            
            # Hourly traffic pattern
            cursor.execute('''
                SELECT 
                    strftime('%H', timestamp) as hour,
                    COUNT(*) as packet_count,
                    SUM(packet_size) as total_bytes
                FROM packets
                WHERE timestamp > datetime('now', '-{} hours')
                GROUP BY strftime('%H', timestamp)
                ORDER BY hour
            '''.format(hours))
            hourly_pattern = [dict(row) for row in cursor.fetchall()]
            
            return {
                'total_packets': total_packets,
                'protocol_distribution': protocol_stats,
                'top_source_ips': top_sources,
                'top_destination_ips': top_destinations,
                'hourly_traffic_pattern': hourly_pattern,
                'query_time_hours': hours
            }
            
        except sqlite3.Error as e:
            logger.error(f"Error getting packet statistics: {e}")
            return {}
    
    def get_threat_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Get threat detection statistics"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Total threats
            cursor.execute("SELECT COUNT(*) FROM threats WHERE detected_at > datetime('now', '-{} hours')".format(hours))
            total_threats = cursor.fetchone()[0]
            
            # Threats by type
            cursor.execute('''
                SELECT threat_type, COUNT(*) as count, AVG(confidence) as avg_confidence
                FROM threats
                WHERE detected_at > datetime('now', '-{} hours')
                GROUP BY threat_type
                ORDER BY count DESC
            '''.format(hours))
            threat_types = [dict(row) for row in cursor.fetchall()]
            
            # Threats by severity
            cursor.execute('''
                SELECT severity, COUNT(*) as count
                FROM threats
                WHERE detected_at > datetime('now', '-{} hours')
                GROUP BY severity
                ORDER BY 
                    CASE severity 
                        WHEN 'Critical' THEN 1
                        WHEN 'High' THEN 2
                        WHEN 'Medium' THEN 3
                        WHEN 'Low' THEN 4
                        ELSE 5
                    END
            '''.format(hours))
            severity_distribution = [dict(row) for row in cursor.fetchall()]
            
            # Recent threats
            cursor.execute('''
                SELECT threat_type, severity, description, src_ip, detected_at, confidence
                FROM threats
                WHERE detected_at > datetime('now', '-{} hours')
                ORDER BY detected_at DESC
                LIMIT 20
            '''.format(hours))
            recent_threats = [dict(row) for row in cursor.fetchall()]
            
            return {
                'total_threats': total_threats,
                'threat_types': threat_types,
                'severity_distribution': severity_distribution,
                'recent_threats': recent_threats,
                'query_time_hours': hours
            }
            
        except sqlite3.Error as e:
            logger.error(f"Error getting threat statistics: {e}")
            return {}
    
    def cleanup_old_data(self, days: int = 30) -> bool:
        """Clean up old data to maintain performance"""
        with self.lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                # Delete old packets
                cursor.execute("DELETE FROM packets WHERE timestamp < datetime('now', '-{} days')".format(days))
                packets_deleted = cursor.rowcount
                
                # Delete old threats
                cursor.execute("DELETE FROM threats WHERE detected_at < datetime('now', '-{} days')".format(days))
                threats_deleted = cursor.rowcount
                
                # Delete old system events
                cursor.execute("DELETE FROM system_events WHERE timestamp < datetime('now', '-{} days')".format(days))
                events_deleted = cursor.rowcount
                
                # Vacuum database to reclaim space
                cursor.execute("VACUUM")
                
                conn.commit()
                
                logger.info(f"Cleanup completed: {packets_deleted} packets, {threats_deleted} threats, {events_deleted} events deleted")
                return True
                
            except sqlite3.Error as e:
                logger.error(f"Database cleanup error: {e}")
                return False
    
    def log_system_event(self, event_type: str, event_data: Dict[str, Any], severity: str = 'INFO'):
        """Log system events for debugging and monitoring"""
        with self.lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                event_data_json = json.dumps(event_data)
                
                cursor.execute('''
                    INSERT INTO system_events (event_type, event_data, severity)
                    VALUES (?, ?, ?)
                ''', (event_type, event_data_json, severity))
                
                conn.commit()
                
            except sqlite3.Error as e:
                logger.error(f"Error logging system event: {e}")
    
    def close(self):
        """Close all database connections"""
        with self.lock:
            for conn in self.connection_pool.values():
                conn.close()
            self.connection_pool.clear()
            logger.info("Database connections closed")
    
    def __del__(self):
        """Destructor to ensure connections are closed"""
        self.close()

# Test the database manager
if __name__ == "__main__":
    # Create test database
    db = DatabaseManager("test_database.db")
    
    # Test packet insertion
    test_packet = {
        'src_ip': '192.168.1.100',
        'dst_ip': '8.8.8.8',
        'src_port': 12345,
        'dst_port': 80,
        'protocol': 'TCP',
        'packet_size': 1024,
        'ttl': 64
    }
    
    packet_id = db.insert_packet(test_packet)
    print(f"✅ Inserted test packet with ID: {packet_id}")
    
    # Test threat insertion
    test_threat = {
        'packet_id': packet_id,
        'type': 'port_scan',
        'severity': 'High',
        'description': 'Test threat detection',
        'src_ip': '192.168.1.100',
        'confidence': 0.95
    }
    
    threat_id = db.insert_threat(test_threat)
    print(f"✅ Inserted test threat with ID: {threat_id}")
    
    # Test statistics
    stats = db.get_packet_statistics()
    print(f"✅ Packet statistics: {stats['total_packets']} packets")
    
    threat_stats = db.get_threat_statistics()
    print(f"✅ Threat statistics: {threat_stats['total_threats']} threats")
    
    print("✅ Database module test completed successfully!")