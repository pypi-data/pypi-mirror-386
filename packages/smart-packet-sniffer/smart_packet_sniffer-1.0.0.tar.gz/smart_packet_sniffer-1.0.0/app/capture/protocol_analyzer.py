"""
Advanced Protocol Analyzer for Deep Packet Inspection
Analyzes various network protocols and extracts meaningful information
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    from scapy.all import DNS, HTTP, Raw, DHCP, SMB, FTP
except ImportError:
    print("Some Scapy modules not available - basic functionality will work")

import re
import json
import logging
from typing import Dict, Any, Optional, List
from collections import defaultdict

logger = logging.getLogger(__name__)

class ProtocolAnalyzer:
    """Advanced protocol analyzer for extracting application-layer information"""
    
    def __init__(self):
        self.supported_protocols = {
            'DNS': self._analyze_dns,
            'HTTP': self._analyze_http,
            'DHCP': self._analyze_dhcp,
            'FTP': self._analyze_ftp,
            'SMTP': self._analyze_smtp
        }
        
        # Common port mappings
        self.port_protocols = {
            53: 'DNS', 80: 'HTTP', 443: 'HTTPS', 21: 'FTP', 22: 'SSH',
            23: 'Telnet', 25: 'SMTP', 110: 'POP3', 143: 'IMAP', 993: 'IMAPS',
            995: 'POP3S', 67: 'DHCP', 68: 'DHCP', 161: 'SNMP', 445: 'SMB'
        }
        
        logger.info("🔍 Protocol analyzer initialized")
    
    def analyze_packet_content(self, packet, packet_model) -> Dict[str, Any]:
        """Analyze packet for application-layer protocols"""
        analysis_results = {
            'application_protocol': 'Unknown',
            'service_info': {},
            'extracted_data': {},
            'security_indicators': []
        }
        
        try:
            # Determine application protocol from port
            dst_port = packet_model.dst_port
            src_port = packet_model.src_port
            
            app_protocol = None
            if dst_port in self.port_protocols:
                app_protocol = self.port_protocols[dst_port]
            elif src_port in self.port_protocols:
                app_protocol = self.port_protocols[src_port]
            
            if app_protocol:
                analysis_results['application_protocol'] = app_protocol
            
            # Deep packet inspection based on protocol
            if DNS in packet:
                analysis_results.update(self._analyze_dns(packet[DNS]))
            elif Raw in packet:
                raw_data = bytes(packet[Raw])
                
                # HTTP analysis
                if dst_port in [80, 443, 8080, 8443] or src_port in [80, 443, 8080, 8443]:
                    http_analysis = self._analyze_http_raw(raw_data)
                    if http_analysis:
                        analysis_results.update(http_analysis)
                
                # FTP analysis
                elif dst_port == 21 or src_port == 21:
                    ftp_analysis = self._analyze_ftp_raw(raw_data)
                    if ftp_analysis:
                        analysis_results.update(ftp_analysis)
                
                # SMTP analysis
                elif dst_port == 25 or src_port == 25:
                    smtp_analysis = self._analyze_smtp_raw(raw_data)
                    if smtp_analysis:
                        analysis_results.update(smtp_analysis)
                
                # Generic payload analysis
                payload_analysis = self._analyze_generic_payload(raw_data)
                analysis_results['extracted_data'].update(payload_analysis)
            
            return analysis_results
            
        except Exception as e:
            logger.error(f"Error in protocol analysis: {e}")
            return analysis_results
    
    def _analyze_dns(self, dns_layer) -> Dict[str, Any]:
        """Analyze DNS packets for queries and responses"""
        analysis = {
            'application_protocol': 'DNS',
            'service_info': {
                'query_id': dns_layer.id,
                'query_type': 'Query' if dns_layer.qr == 0 else 'Response',
                'opcode': dns_layer.opcode,
                'response_code': dns_layer.rcode if hasattr(dns_layer, 'rcode') else None
            },
            'extracted_data': {
                'dns_queries': [],
                'dns_responses': []
            },
            'security_indicators': []
        }
        
        # Extract queries
        if hasattr(dns_layer, 'qd') and dns_layer.qd:
            for query in dns_layer.qd:
                query_info = {
                    'name': query.qname.decode('utf-8', errors='ignore').rstrip('.'),
                    'type': query.qtype,
                    'class': query.qclass
                }
                analysis['extracted_data']['dns_queries'].append(query_info)
                
                # Security analysis
                domain = query_info['name']
                if self._is_suspicious_domain(domain):
                    analysis['security_indicators'].append(f"Suspicious domain: {domain}")
        
        # Extract responses
        if hasattr(dns_layer, 'an') and dns_layer.an:
            for answer in dns_layer.an:
                if hasattr(answer, 'rdata'):
                    response_info = {
                        'name': answer.rrname.decode('utf-8', errors='ignore').rstrip('.'),
                        'type': answer.type,
                        'data': str(answer.rdata)
                    }
                    analysis['extracted_data']['dns_responses'].append(response_info)
        
        return analysis
    
    def _analyze_http_raw(self, raw_data: bytes) -> Optional[Dict[str, Any]]:
        """Analyze raw HTTP data"""
        try:
            data_str = raw_data.decode('utf-8', errors='ignore')
            
            analysis = {
                'application_protocol': 'HTTP',
                'service_info': {},
                'extracted_data': {
                    'http_method': None,
                    'http_uri': None,
                    'http_version': None,
                    'headers': {},
                    'user_agent': None,
                    'referer': None
                },
                'security_indicators': []
            }
            
            lines = data_str.split('\r\n')
            if not lines:
                return None
            
            # Parse request line
            request_line = lines[0]
            if any(method in request_line for method in ['GET', 'POST', 'PUT', 'DELETE', 'HEAD', 'OPTIONS']):
                parts = request_line.split(' ')
                if len(parts) >= 3:
                    analysis['extracted_data']['http_method'] = parts[0]
                    analysis['extracted_data']['http_uri'] = parts[1]
                    analysis['extracted_data']['http_version'] = parts[2]
            
            # Parse headers
            for line in lines[1:]:
                if ':' in line:
                    header, value = line.split(':', 1)
                    header = header.strip().lower()
                    value = value.strip()
                    
                    analysis['extracted_data']['headers'][header] = value
                    
                    if header == 'user-agent':
                        analysis['extracted_data']['user_agent'] = value
                        if self._is_suspicious_user_agent(value):
                            analysis['security_indicators'].append(f"Suspicious User-Agent: {value}")
                    
                    elif header == 'referer':
                        analysis['extracted_data']['referer'] = value
            
            # Security analysis
            if analysis['extracted_data']['http_uri']:
                uri = analysis['extracted_data']['http_uri']
                if self._has_suspicious_patterns(uri):
                    analysis['security_indicators'].append(f"Suspicious URI pattern: {uri}")
            
            return analysis
            
        except Exception as e:
            logger.debug(f"HTTP analysis error: {e}")
            return None
    
    def _analyze_ftp_raw(self, raw_data: bytes) -> Optional[Dict[str, Any]]:
        """Analyze raw FTP data"""
        try:
            data_str = raw_data.decode('utf-8', errors='ignore')
            
            analysis = {
                'application_protocol': 'FTP',
                'service_info': {},
                'extracted_data': {
                    'ftp_command': None,
                    'ftp_response': None,
                    'username': None,
                    'filename': None
                },
                'security_indicators': []
            }
            
            # FTP commands
            ftp_commands = ['USER', 'PASS', 'RETR', 'STOR', 'LIST', 'PWD', 'CWD', 'QUIT']
            for command in ftp_commands:
                if data_str.startswith(command):
                    parts = data_str.split(' ', 1)
                    analysis['extracted_data']['ftp_command'] = parts[0]
                    if len(parts) > 1:
                        if command == 'USER':
                            analysis['extracted_data']['username'] = parts[1].strip()
                        elif command in ['RETR', 'STOR']:
                            analysis['extracted_data']['filename'] = parts[1].strip()
            
            # FTP responses (3-digit codes)
            if re.match(r'^\d{3}', data_str):
                analysis['extracted_data']['ftp_response'] = data_str.split('\r\n')[0]
            
            # Security indicators
            if 'anonymous' in data_str.lower():
                analysis['security_indicators'].append("Anonymous FTP access detected")
            
            return analysis
            
        except Exception as e:
            logger.debug(f"FTP analysis error: {e}")
            return None
    
    def _analyze_smtp_raw(self, raw_data: bytes) -> Optional[Dict[str, Any]]:
        """Analyze raw SMTP data"""
        try:
            data_str = raw_data.decode('utf-8', errors='ignore')
            
            analysis = {
                'application_protocol': 'SMTP',
                'service_info': {},
                'extracted_data': {
                    'smtp_command': None,
                    'email_from': None,
                    'email_to': None,
                    'subject': None
                },
                'security_indicators': []
            }
            
            # SMTP commands
            smtp_commands = ['HELO', 'EHLO', 'MAIL FROM', 'RCPT TO', 'DATA', 'QUIT']
            for command in smtp_commands:
                if command in data_str.upper():
                    analysis['extracted_data']['smtp_command'] = command
                    
                    if 'MAIL FROM:' in data_str.upper():
                        match = re.search(r'MAIL FROM:\s*<(.+?)>', data_str, re.IGNORECASE)
                        if match:
                            analysis['extracted_data']['email_from'] = match.group(1)
                    
                    elif 'RCPT TO:' in data_str.upper():
                        match = re.search(r'RCPT TO:\s*<(.+?)>', data_str, re.IGNORECASE)
                        if match:
                            analysis['extracted_data']['email_to'] = match.group(1)
            
            # Email headers
            if 'Subject:' in data_str:
                match = re.search(r'Subject:\s*(.+)', data_str, re.IGNORECASE)
                if match:
                    analysis['extracted_data']['subject'] = match.group(1).strip()
            
            return analysis
            
        except Exception as e:
            logger.debug(f"SMTP analysis error: {e}")
            return None
    
    def _analyze_generic_payload(self, raw_data: bytes) -> Dict[str, Any]:
        """Generic payload analysis for security indicators"""
        analysis = {
            'payload_size': len(raw_data),
            'contains_binary': False,
            'suspicious_strings': [],
            'encoded_data': False
        }
        
        try:
            # Check for binary data
            try:
                data_str = raw_data.decode('utf-8')
                analysis['contains_binary'] = False
            except UnicodeDecodeError:
                analysis['contains_binary'] = True
                data_str = raw_data.decode('utf-8', errors='ignore')
            
            # Look for suspicious patterns
            suspicious_patterns = [
                r'<script.*?>.*?</script>',  # JavaScript
                r'eval\s*\(',                # eval() calls
                r'exec\s*\(',                # exec() calls
                r'system\s*\(',              # system() calls
                r'/bin/sh',                  # Shell references
                r'cmd\.exe',                 # Windows command shell
                r'powershell',               # PowerShell
                r'SELECT.*FROM',             # SQL injection
                r'UNION.*SELECT',            # SQL injection
                r'DROP.*TABLE',              # SQL injection
                r'base64|b64encode',         # Encoding
                r'%[0-9a-fA-F]{2}',         # URL encoding
            ]
            
            for pattern in suspicious_patterns:
                matches = re.findall(pattern, data_str, re.IGNORECASE | re.DOTALL)
                if matches:
                    analysis['suspicious_strings'].extend(matches[:3])  # Limit to 3 matches
            
            # Check for common encodings
            if re.search(r'[A-Za-z0-9+/]{20,}={0,2}', data_str):
                analysis['encoded_data'] = True
            
        except Exception as e:
            logger.debug(f"Generic payload analysis error: {e}")
        
        return analysis
    
    def _is_suspicious_domain(self, domain: str) -> bool:
        """Check if domain name appears suspicious"""
        suspicious_indicators = [
            len(domain) > 50,  # Very long domain
            domain.count('.') > 5,  # Too many subdomains
            re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', domain),  # IP as domain
            any(char in domain for char in ['_', '--', '..']),  # Suspicious characters
            len(domain.replace('.', '').replace('-', '')) < 4,  # Very short
            domain.endswith('.tk') or domain.endswith('.ml'),  # Suspicious TLDs
        ]
        
        return any(suspicious_indicators)
    
    def _is_suspicious_user_agent(self, user_agent: str) -> bool:
        """Check if User-Agent string appears suspicious"""
        suspicious_patterns = [
            r'bot|crawler|spider',  # Bots
            r'curl|wget|python|perl',  # Command line tools
            r'^.{0,10}$',  # Too short
            r'^.{200,}$',  # Too long
            r'[<>{}]',  # HTML/script tags
        ]
        
        return any(re.search(pattern, user_agent, re.IGNORECASE) for pattern in suspicious_patterns)
    
    def _has_suspicious_patterns(self, uri: str) -> bool:
        """Check URI for suspicious patterns"""
        suspicious_patterns = [
            r'\.\./.*\.\.',  # Directory traversal
            r'%2e%2e%2f',    # Encoded directory traversal
            r'<script',       # XSS attempt
            r'javascript:',   # JavaScript protocol
            r'data:',         # Data protocol
            r'eval\(',        # eval() function
            r'system\(',      # system() function
            r'exec\(',        # exec() function
        ]
        
        return any(re.search(pattern, uri, re.IGNORECASE) for pattern in suspicious_patterns)

# Test the protocol analyzer
if __name__ == "__main__":
    analyzer = ProtocolAnalyzer()
    
    # Test with some sample data
    print("✅ Protocol analyzer initialized successfully!")
    print(f"📊 Supported protocols: {list(analyzer.supported_protocols.keys())}")
    print(f"🔍 Monitored ports: {list(analyzer.port_protocols.keys())}")