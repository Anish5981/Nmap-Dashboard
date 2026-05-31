"""
Nmap Scan Executor Module

Handles input validation, command construction, and subprocess execution
for all supported Nmap scan types.
"""

import os
import re
import uuid
import subprocess
import time
from datetime import datetime


# Strict regex: only allow safe characters in target input
VALID_TARGET_PATTERN = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9.\-:/,\s]*$')

# All 15 mandatory scan types from the assignment
SCAN_TYPES = {
    'ping_scan': {
        'name': 'Ping Scan',
        'description': 'Discover hosts without port scanning',
        'flags': ['-sn'],
    },
    'fast_scan': {
        'name': 'Fast Scan',
        'description': 'Scan the 100 most common ports quickly',
        'flags': ['-F'],
    },
    'service_version': {
        'name': 'Service Version Detection',
        'description': 'Detect service versions on open ports',
        'flags': ['-sV'],
    },
    'os_detection': {
        'name': 'OS Detection',
        'description': 'Attempt to identify the operating system',
        'flags': ['-O'],
    },
    'tcp_syn': {
        'name': 'TCP SYN Scan',
        'description': 'Stealthy half-open TCP scan (requires privileges)',
        'flags': ['-sS'],
    },
    'tcp_connect': {
        'name': 'TCP Connect Scan',
        'description': 'Full TCP connection scan',
        'flags': ['-sT'],
    },
    'udp_scan': {
        'name': 'UDP Scan',
        'description': 'Scan UDP ports (slower, may require privileges)',
        'flags': ['-sU'],
    },
    'aggressive_scan': {
        'name': 'Aggressive Scan',
        'description': 'OS detection, version, scripts, and traceroute',
        'flags': ['-A'],
    },
    'specific_ports': {
        'name': 'Scan Specific Ports',
        'description': 'Scan ports 22 (SSH), 80 (HTTP), and 443 (HTTPS)',
        'flags': ['-p', '22,80,443'],
    },
    'top_ports': {
        'name': 'Top 100 Ports Scan',
        'description': 'Scan the 100 most commonly used ports',
        'flags': ['--top-ports', '100'],
    },
    'full_port': {
        'name': 'Full Port Scan',
        'description': 'Scan all 65535 ports (very slow)',
        'flags': ['-p-'],
    },
    'http_title': {
        'name': 'Detect HTTP Title',
        'description': 'Run the http-title NSE script',
        'flags': ['--script', 'http-title'],
    },
    'vuln_scan': {
        'name': 'Vulnerability Script Scan',
        'description': 'Run vulnerability detection scripts',
        'flags': ['--script', 'vuln'],
    },
    'network_range': {
        'name': 'Network Range Scan',
        'description': 'Discover hosts in a network range (use CIDR notation)',
        'flags': [],
    },
    'save_xml': {
        'name': 'Service Scan with XML Output',
        'description': 'Service version detection with explicit XML save',
        'flags': ['-sV'],
    },
}


def validate_target(target):
    """
    Validate user-provided scan target.

    Returns:
        (bool, str): (is_valid, error_message)
    """
    if not target:
        return False, 'Target cannot be empty.'

    target = target.strip()

    if len(target) > 255:
        return False, 'Target is too long (max 255 characters).'

    if not VALID_TARGET_PATTERN.match(target):
        return False, 'Target contains invalid characters. Only letters, numbers, dots, hyphens, colons, slashes, and commas are allowed.'

    # Check for shell injection attempts
    dangerous_chars = [';', '|', '&', '$', '`', '(', ')', '{', '}', '<', '>', '!', '~']
    for char in dangerous_chars:
        if char in target:
            return False, f'Target contains forbidden character: {char}'

    return True, ''


def is_private_target(target):
    """Check if the target appears to be a private/local address."""
    private_patterns = [
        r'^10\.',
        r'^172\.(1[6-9]|2[0-9]|3[0-1])\.',
        r'^192\.168\.',
        r'^127\.',
        r'^localhost',
        r'^::1',
        r'^fe80:',
    ]
    for pattern in private_patterns:
        if re.match(pattern, target, re.IGNORECASE):
            return True
    return False


def execute_scan(target, scan_type_key, nmap_path, scans_dir, timeout=300):
    """
    Execute an Nmap scan.

    Args:
        target: IP address, hostname, or CIDR range
        scan_type_key: Key from SCAN_TYPES dict
        nmap_path: Path to the nmap executable
        scans_dir: Directory to store XML output files
        timeout: Maximum scan duration in seconds

    Returns:
        dict with keys: success, xml_path, command, duration, error
    """
    # Validate scan type
    if scan_type_key not in SCAN_TYPES:
        return {
            'success': False,
            'error': f'Unknown scan type: {scan_type_key}',
        }

    # Validate target
    is_valid, error_msg = validate_target(target)
    if not is_valid:
        return {
            'success': False,
            'error': error_msg,
        }

    target = target.strip()

    # Ensure scans directory exists
    os.makedirs(scans_dir, exist_ok=True)

    # Generate unique filename for XML output
    xml_filename = f"{scan_type_key}_{uuid.uuid4().hex[:8]}.xml"
    xml_path = os.path.join(scans_dir, xml_filename)

    # Build command
    scan_config = SCAN_TYPES[scan_type_key]
    cmd = [nmap_path] + scan_config['flags'] + ['-oX', xml_path, target]

    # Build the human-readable command string (for display)
    display_cmd = 'nmap ' + ' '.join(scan_config['flags'] + [target])

    result = {
        'success': False,
        'xml_path': xml_path,
        'xml_filename': xml_filename,
        'command': display_cmd,
        'duration': 0,
        'error': None,
    }

    try:
        start_time = time.time()

        # Execute Nmap — NEVER use shell=True
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False,
        )

        duration = round(time.time() - start_time, 2)
        result['duration'] = duration

        if proc.returncode == 0:
            result['success'] = True
        else:
            # Nmap may return non-zero but still produce output
            if os.path.exists(xml_path) and os.path.getsize(xml_path) > 0:
                result['success'] = True
            else:
                result['error'] = proc.stderr or f'Nmap exited with code {proc.returncode}'

    except subprocess.TimeoutExpired:
        result['error'] = f'Scan timed out after {timeout} seconds.'
        result['duration'] = timeout

    except FileNotFoundError:
        result['error'] = (
            f'Nmap not found at: {nmap_path}. '
            'Please install Nmap from https://nmap.org/download.html'
        )

    except Exception as e:
        result['error'] = f'Unexpected error: {str(e)}'

    return result
