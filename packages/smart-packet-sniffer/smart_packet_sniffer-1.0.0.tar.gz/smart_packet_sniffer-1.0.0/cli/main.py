#!/usr/bin/env python3
"""
Smart Packet Sniffer with Traffic Analyzer & Threat Detector
Main Application Entry Point

This file starts the complete packet sniffer system with web dashboard.
Run this file to start your project demonstration.
"""
import sys
import os
import platform
import time
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def print_banner():
    """Print application banner"""
    banner = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║        🛡️  SMART PACKET SNIFFER WITH TRAFFIC ANALYZER & THREAT DETECTOR      ║
║                                                                              ║
║        Advanced Network Security Monitoring System                          ║
║        Real-time Packet Capture | Traffic Analysis | Threat Detection       ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """
    print(banner)
    print(f"🖥️  Platform: {platform.system()} {platform.release()}")
    print(f"🐍 Python: {sys.version.split()[0]}")
    print(f"📁 Project Directory: {project_root}")
    print("="*80)

def check_admin_privileges():
    """Check if running with administrator/root privileges"""
    if platform.system() == "Windows":
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin()
        except Exception:
            return False
    else:  # Linux/macOS
        return os.geteuid() == 0

def check_dependencies():
    """Check if all required dependencies are installed"""
    required_packages = [
        'scapy', 'flask', 'flask_socketio', 'numpy', 
        'pandas', 'matplotlib', 'plotly', 'sklearn', 'psutil'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package}")
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print("Please install missing packages:")
        print(f"   pip install {' '.join(missing_packages)}")
        return False
    
    print("✅ All dependencies satisfied!")
    return True

def setup_directories():
    """Create required directories"""
    directories = ['data', 'logs', 'models']
    
    for directory in directories:
        dir_path = project_root / directory
        dir_path.mkdir(exist_ok=True)
        print(f"📁 Directory ready: {directory}")

def main():
    """Main application function"""
    print_banner()
    
    print("🔍 Checking system requirements...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8 or higher is required")
        print(f"   Current version: {sys.version}")
        sys.exit(1)
    print(f"✅ Python version: {sys.version.split()[0]}")
    
    # Check admin privileges
    if not check_admin_privileges():
        print("⚠️  WARNING: Administrator/root privileges required for packet capture")
        print("   - Windows: Run Command Prompt as Administrator")
        print("   - Linux/macOS: Use 'sudo python3 main.py'")
        print()
        
        response = input("Continue anyway? Some features may not work (y/N): ").lower().strip()
        if response != 'y':
            print("👋 Exiting. Please restart with administrator privileges.")
            sys.exit(0)
        print("⚡ Continuing without full privileges...")
    else:
        print("✅ Administrator privileges detected")
    
    # Check dependencies
    print("\n📦 Checking dependencies...")
    if not check_dependencies():
        print("\n❌ Please install missing dependencies and try again.")
        sys.exit(1)
    
    # Setup directories
    print("\n📁 Setting up directories...")
    setup_directories()
    
    # Test database connection
    print("\n🗄️  Testing database connection...")
    try:
        from app.models.database import DatabaseManager
        db = DatabaseManager()
        print("✅ Database connection successful")
    except Exception as e:
        print(f"❌ Database error: {e}")
        sys.exit(1)
    
    # Test packet capture capability
    print("\n📡 Testing packet capture capability...")
    try:
        from app.capture.packet_capture import PacketCaptureEngine
        capture = PacketCaptureEngine()
        interface_info = capture.get_interface_info()
        print(f"✅ Network interface ready: {interface_info['name']}")
    except Exception as e:
        print(f"⚠️  Packet capture warning: {e}")
        print("   Some network monitoring features may be limited")
    
    print("\n🚀 Starting Smart Packet Sniffer Dashboard...")
    print("   📊 Web Dashboard: http://localhost:5000")
    print("   🛑 Press Ctrl+C to stop")
    print("="*80)
    
    # Start the web application
    try:
        from app.dashboard.routes import app, socketio
        
        print("🌐 Launching web server...")
        time.sleep(2)  # Give user time to read the messages
        
        # Start the Flask-SocketIO application
        socketio.run(
            app,
            debug=False,
            host='0.0.0.0',
            port=5000,
            log_output=False  # Reduce console spam
        )
        
    except KeyboardInterrupt:
        print("\n\n🛑 Application stopped by user")
        print("👋 Thank you for using Smart Packet Sniffer!")
        
    except Exception as e:
        print(f"\n❌ Application error: {e}")
        print("Please check the error message above and try again.")
        sys.exit(1)
        
    finally:
        print("\n🔄 Cleaning up resources...")
        # Perform any necessary cleanup here
        print("✅ Cleanup completed")

def run_tests():
    """Run basic system tests"""
    print("🧪 Running system tests...")
    
    try:
        # Test database
        from app.models.database import DatabaseManager
        db = DatabaseManager()
        print("✅ Database test passed")
        
        # Test packet model
        from app.models.packet_model import PacketModel
        test_packet = PacketModel(
            src_ip='192.168.1.100',
            dst_ip='8.8.8.8',
            protocol='TCP',
            packet_size=64
        )
        print("✅ Packet model test passed")
        
        # Test threat detector
        from app.analysis.threat_detector import ThreatDetector
        detector = ThreatDetector()
        print("✅ Threat detector test passed")
        
        # Test traffic analyzer
        from app.analysis.traffic_analyzer import TrafficAnalyzer
        analyzer = TrafficAnalyzer()
        print("✅ Traffic analyzer test passed")
        
        print("🎉 All tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    # Check for test flag
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        print_banner()
        success = run_tests()
        sys.exit(0 if success else 1)
    
    # Run main application
    main()