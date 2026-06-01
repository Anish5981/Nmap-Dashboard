"""
API Routes

JSON API endpoints for AJAX calls and programmatic access.
"""

from flask import Blueprint, jsonify, request
from models import db, Scan, Host, Port
from flask_login import login_required

api_bp = Blueprint('api', __name__)


@api_bp.route('/api/stats')
@login_required
def stats():
    """Dashboard summary statistics."""
    total_scans = Scan.query.count()
    total_hosts = Host.query.count()
    total_open_ports = Port.query.filter_by(port_state='open').count()
    completed_scans = Scan.query.filter_by(status='completed').count()
    failed_scans = Scan.query.filter_by(status='failed').count()

    return jsonify({
        'total_scans': total_scans,
        'total_hosts': total_hosts,
        'total_open_ports': total_open_ports,
        'completed_scans': completed_scans,
        'failed_scans': failed_scans,
    })


@api_bp.route('/api/scans')
@login_required
def list_scans():
    """List scans with optional filters."""
    target = request.args.get('target', '').strip()
    scan_type = request.args.get('type', '').strip()

    query = Scan.query

    if target:
        query = query.filter(Scan.target.like(f'%{target}%'))
    if scan_type:
        query = query.filter(Scan.scan_type == scan_type)

    scans = query.order_by(Scan.scan_time.desc()).limit(100).all()
    return jsonify([s.to_dict() for s in scans])


@api_bp.route('/api/scans/<int:scan_id>')
@login_required
def get_scan(scan_id):
    """Get detailed scan info with hosts and ports."""
    scan = Scan.query.get_or_404(scan_id)
    data = scan.to_dict()
    data['hosts'] = [h.to_dict() for h in scan.hosts]
    return jsonify(data)


@api_bp.route('/api/search')
@login_required
def search():
    """Global search across hosts, ports, and services."""
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify({'hosts': [], 'ports': []})

    # Search hosts by IP or hostname
    hosts = Host.query.filter(
        db.or_(
            Host.ip_address.like(f'%{q}%'),
            Host.hostname.like(f'%{q}%'),
        )
    ).limit(50).all()

    # Search ports by number or service name
    port_query = Port.query
    try:
        port_num = int(q)
        port_query = port_query.filter(Port.port_number == port_num)
    except ValueError:
        port_query = port_query.filter(
            db.or_(
                Port.service_name.like(f'%{q}%'),
                Port.service_version.like(f'%{q}%'),
            )
        )
    ports = port_query.limit(50).all()

    return jsonify({
        'hosts': [h.to_dict() for h in hosts],
        'ports': [p.to_dict() for p in ports],
    })
