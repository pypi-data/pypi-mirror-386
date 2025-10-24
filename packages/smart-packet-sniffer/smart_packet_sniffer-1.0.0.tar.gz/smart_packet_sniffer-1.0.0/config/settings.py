"""
Configuration settings for Smart Packet Sniffer
"""
import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent.parent

# Database settings
DATABASE_PATH = BASE_DIR / 'data' / 'network_data.db'
LOG_PATH = BASE_DIR / 'logs' / 'system.log'

# Network settings
DEFAULT_INTERFACE = None  # Auto-detect
PACKET_BUFFER_SIZE = 10000
CAPTURE_TIMEOUT = 1.0

# Web dashboard settings
WEB_HOST = '0.0.0.0'
WEB_PORT = 5000
SECRET_KEY = 'smart-packet-sniffer-secret-key-change-in-production'

# Threat detection settings
PORT_SCAN_THRESHOLD = 5
HIGH_TRAFFIC_THRESHOLD = 100
SUSPICIOUS_PORTS = [22, 23, 135, 139, 445, 1433, 3389, 5432]

# Analysis settings
ANALYSIS_WINDOW_SECONDS = 300
CLEANUP_DAYS = 30

# Logging settings
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Create directories if they don't exist
os.makedirs(BASE_DIR / 'data', exist_ok=True)
os.makedirs(BASE_DIR / 'logs', exist_ok=True)
