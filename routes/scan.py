"""
Scan Routes

Handles scan execution, detail views, and host detail views.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from models import db, Scan, Host, Port
from modules.scanner import SCAN_TYPES, execute_scan, validate_target, is_private_target
from modules.parser import parse_nmap_xml
from datetime import datetime

scan_bp = Blueprint('scan', __name__)


@scan_bp.route('/scan/new')
def new_scan():
    """Render the new scan form."""
    return render_template('new_scan.html', scan_types=SCAN_TYPES)


import threading

def _run_scan_thread(app, scan_id, target, scan_type_key, nmap_path, scans_dir, timeout):
    """Background task to run a single scan and save results."""
    with app.app_context():
        scan_record = Scan.query.get(scan_id)
        if not scan_record:
            return

        # Execute the scan
        result = execute_scan(
            target=target,
            scan_type_key=scan_type_key,
            nmap_path=nmap_path,
            scans_dir=scans_dir,
            timeout=timeout,
        )

        # Update scan record with results
        scan_record.command_used = result.get('command', '')
        scan_record.raw_xml_path = result.get('xml_filename', '')
        scan_record.duration_seconds = result.get('duration', 0)

        if result['success']:
            # Parse the XML output
            hosts_data = parse_nmap_xml(result['xml_path'])

            # Store parsed data in database
            for host_data in hosts_data:
                host = Host(
                    scan_id=scan_record.id,
                    ip_address=host_data['ip_address'],
                    hostname=host_data.get('hostname'),
                    host_status=host_data.get('host_status', 'up'),
                    os_details=host_data.get('os_details'),
                )
                db.session.add(host)
                db.session.flush()  # Get the host.id

                for port_data in host_data.get('ports', []):
                    port = Port(
                        host_id=host.id,
                        port_number=port_data['port_number'],
                        protocol=port_data.get('protocol', 'tcp'),
                        port_state=port_data.get('port_state', 'open'),
                        service_name=port_data.get('service_name'),
                        service_version=port_data.get('service_version'),
                        script_output=port_data.get('script_output'),
                    )
                    db.session.add(port)

            scan_record.status = 'completed'
            db.session.commit()
        else:
            error = result.get('error', 'Unknown error')
            if 'timed out' in str(error).lower():
                scan_record.status = 'timeout'
            else:
                scan_record.status = 'failed'
            db.session.commit()


@scan_bp.route('/scan/execute', methods=['POST'])
def execute():
    """Execute one or more scans and redirect."""
    target = request.form.get('target', '').strip()
    scan_types_raw = request.form.get('scan_type', '').strip()

    # Validate target
    is_valid, error_msg = validate_target(target)
    if not is_valid:
        flash(f'Invalid target: {error_msg}', 'danger')
        return redirect(url_for('scan.new_scan'))

    if not scan_types_raw:
        flash('No scan type selected.', 'danger')
        return redirect(url_for('scan.new_scan'))

    # Process multiple scan types
    scan_type_keys = [k for k in scan_types_raw.split(',') if k in SCAN_TYPES]
    
    if not scan_type_keys:
        flash('Invalid scan type selected.', 'danger')
        return redirect(url_for('scan.new_scan'))

    # Warn about public targets
    if not is_private_target(target):
        flash(
            'Warning: You are scanning a non-private target. '
            'Only scan networks you have permission to scan.',
            'warning'
        )

    # For a single scan, we'll block and wait so we can redirect directly to it
    if len(scan_type_keys) == 1:
        scan_type_key = scan_type_keys[0]
        scan_config = SCAN_TYPES[scan_type_key]
        
        scan_record = Scan(
            target=target,
            scan_type=scan_config['name'],
            command_used='',
            scan_time=datetime.utcnow(),
            raw_xml_path='',
            status='running',
        )
        db.session.add(scan_record)
        db.session.commit()

        # Run synchronously
        app = current_app._get_current_object()
        _run_scan_thread(app, scan_record.id, target, scan_type_key, 
                         app.config['NMAP_PATH'], app.config['SCANS_DIR'], app.config['SCAN_TIMEOUT'])
        
        # Check status after sync run to set flash message
        db.session.commit()  # Reset transaction snapshot to see thread changes
        db.session.refresh(scan_record)
        if scan_record.status == 'completed':
            flash('Scan completed successfully!', 'success')
        else:
            flash('Scan failed or timed out.', 'danger')
            
        return redirect(url_for('scan.scan_detail', scan_id=scan_record.id))

    # For multiple scans, spawn background threads and redirect to dashboard
    else:
        app = current_app._get_current_object()
        
        for scan_type_key in scan_type_keys:
            scan_config = SCAN_TYPES[scan_type_key]
            
            scan_record = Scan(
                target=target,
                scan_type=scan_config['name'],
                command_used='',
                scan_time=datetime.utcnow(),
                raw_xml_path='',
                status='running',
            )
            db.session.add(scan_record)
            db.session.commit()
            
            # Start background thread for this scan
            thread = threading.Thread(
                target=_run_scan_thread,
                args=(app, scan_record.id, target, scan_type_key,
                      app.config['NMAP_PATH'], app.config['SCANS_DIR'], app.config['SCAN_TIMEOUT'])
            )
            thread.daemon = True
            thread.start()

        flash(f'{len(scan_type_keys)} scans started in the background. Check their status below.', 'info')
        return redirect(url_for('dashboard.index'))


@scan_bp.route('/scan/<int:scan_id>')
def scan_detail(scan_id):
    """Show detailed results for a specific scan."""
    scan = Scan.query.get_or_404(scan_id)
    hosts = Host.query.filter_by(scan_id=scan_id).all()

    return render_template(
        'scan_detail.html',
        scan=scan,
        hosts=hosts,
    )


@scan_bp.route('/host/<int:host_id>')
def host_detail(host_id):
    """Show detailed information for a specific host."""
    host = Host.query.get_or_404(host_id)
    scan = Scan.query.get_or_404(host.scan_id)
    ports = Port.query.filter_by(host_id=host_id).order_by(Port.port_number).all()

    # List of ports commonly targeted by attackers
    RISKY_PORTS = [20, 21, 22, 23, 25, 53, 135, 137, 139, 445, 1433, 3306, 3389]

    return render_template(
        'host_detail.html',
        host=host,
        scan=scan,
        ports=ports,
        risky_ports=RISKY_PORTS,
    )
