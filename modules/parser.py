"""
Nmap XML Parser Module

Parses Nmap XML output files and extracts host, port, service,
and OS information into structured data.
"""

import xml.etree.ElementTree as ET


def parse_nmap_xml(xml_path):
    """
    Parse an Nmap XML output file.

    Args:
        xml_path: Path to the XML file

    Returns:
        list of dicts, each representing a host with its ports:
        [
            {
                'ip_address': '192.168.1.1',
                'hostname': 'router.local',
                'host_status': 'up',
                'os_details': 'Linux 3.x',
                'ports': [
                    {
                        'port_number': 80,
                        'protocol': 'tcp',
                        'port_state': 'open',
                        'service_name': 'http',
                        'service_version': 'Apache 2.4.41',
                        'script_output': '...',
                    },
                    ...
                ]
            },
            ...
        ]
    """
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"XML Parse Error: {e}")
        return []
    except FileNotFoundError:
        print(f"XML file not found: {xml_path}")
        return []

    hosts = []

    for host_elem in root.findall('.//host'):
        host_data = _parse_host(host_elem)
        if host_data:
            hosts.append(host_data)

    return hosts


def _parse_host(host_elem):
    """Parse a single <host> element from Nmap XML."""

    # Extract host status
    status_elem = host_elem.find('status')
    if status_elem is None:
        return None

    host_status = status_elem.get('state', 'down')

    # Extract IP address
    ip_address = None
    for addr_elem in host_elem.findall('address'):
        addr_type = addr_elem.get('addrtype', '')
        if addr_type in ('ipv4', 'ipv6'):
            ip_address = addr_elem.get('addr', '')
            break

    if not ip_address:
        return None

    # Extract hostname
    hostname = None
    hostnames_elem = host_elem.find('hostnames')
    if hostnames_elem is not None:
        hostname_elem = hostnames_elem.find('hostname')
        if hostname_elem is not None:
            hostname = hostname_elem.get('name', '')

    # Extract OS details
    os_details = _parse_os_details(host_elem)

    # Extract ports
    ports = _parse_ports(host_elem)

    return {
        'ip_address': ip_address,
        'hostname': hostname,
        'host_status': host_status if host_status in ('up', 'down') else 'down',
        'os_details': os_details,
        'ports': ports,
    }


def _parse_os_details(host_elem):
    """Extract OS detection details from a host element."""
    os_elem = host_elem.find('os')
    if os_elem is None:
        return None

    os_parts = []

    # Get OS matches
    for osmatch in os_elem.findall('osmatch'):
        name = osmatch.get('name', '')
        accuracy = osmatch.get('accuracy', '')
        if name:
            os_parts.append(f"{name} ({accuracy}% accuracy)" if accuracy else name)

    # Get OS classes as fallback
    if not os_parts:
        for osclass in os_elem.findall('.//osclass'):
            vendor = osclass.get('vendor', '')
            osfamily = osclass.get('osfamily', '')
            osgen = osclass.get('osgen', '')
            parts = [p for p in [vendor, osfamily, osgen] if p]
            if parts:
                os_parts.append(' '.join(parts))

    return '; '.join(os_parts) if os_parts else None


def _parse_ports(host_elem):
    """Extract port information from a host element."""
    ports = []

    ports_elem = host_elem.find('ports')
    if ports_elem is None:
        return ports

    for port_elem in ports_elem.findall('port'):
        port_data = _parse_single_port(port_elem)
        if port_data:
            ports.append(port_data)

    return ports


def _parse_single_port(port_elem):
    """Parse a single <port> element."""
    port_number = port_elem.get('portid', '')
    protocol = port_elem.get('protocol', 'tcp')

    if not port_number:
        return None

    try:
        port_number = int(port_number)
    except ValueError:
        return None

    # Port state
    state_elem = port_elem.find('state')
    port_state = 'filtered'
    if state_elem is not None:
        state = state_elem.get('state', 'filtered')
        if state in ('open', 'closed', 'filtered'):
            port_state = state
        elif 'open' in state:
            port_state = 'open'
        elif 'closed' in state:
            port_state = 'closed'

    # Service info
    service_name = None
    service_version = None
    service_elem = port_elem.find('service')
    if service_elem is not None:
        service_name = service_elem.get('name', None)
        version_parts = []
        product = service_elem.get('product', '')
        version = service_elem.get('version', '')
        extrainfo = service_elem.get('extrainfo', '')
        if product:
            version_parts.append(product)
        if version:
            version_parts.append(version)
        if extrainfo:
            version_parts.append(f'({extrainfo})')
        service_version = ' '.join(version_parts) if version_parts else None

    # Script output
    script_output = _parse_scripts(port_elem)

    return {
        'port_number': port_number,
        'protocol': protocol,
        'port_state': port_state,
        'service_name': service_name,
        'service_version': service_version,
        'script_output': script_output,
    }


def _parse_scripts(elem):
    """Extract NSE script output from an element."""
    scripts = []
    for script_elem in elem.findall('script'):
        script_id = script_elem.get('id', 'unknown')
        script_out = script_elem.get('output', '')
        if script_out:
            scripts.append(f"[{script_id}] {script_out}")

    return '\n'.join(scripts) if scripts else None
