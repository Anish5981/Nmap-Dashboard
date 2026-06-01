"""
Dashboard Routes

Handles the main dashboard homepage and scan history views.
"""

from flask import Blueprint, render_template, request, Response, jsonify, flash, redirect, url_for
import csv
from io import StringIO
from models import db, Scan, Host, Port
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from flask_login import login_required

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    """Dashboard homepage with summary stats and recent scans."""
    # Summary statistics
    total_scans = Scan.query.count()
    total_hosts = Host.query.count()
    total_open_ports = Port.query.filter_by(port_state='open').count()

    # Recent scans (latest 10)
    recent_scans = Scan.query.order_by(Scan.scan_time.desc()).limit(10).all()

    return render_template(
        'dashboard.html',
        total_scans=total_scans,
        total_hosts=total_hosts,
        total_open_ports=total_open_ports,
        recent_scans=recent_scans,
    )


@dashboard_bp.route('/history')
@login_required
def history():
    """Full scan history with pagination."""
    page = request.args.get('page', 1, type=int)
    per_page = 20

    # Optional filters
    target_filter = request.args.get('target', '').strip()
    type_filter = request.args.get('type', '').strip()
    status_filter = request.args.get('status', '').strip()

    query = Scan.query

    if target_filter:
        query = query.filter(Scan.target.like(f'%{target_filter}%'))
    if type_filter:
        query = query.filter(Scan.scan_type == type_filter)
    if status_filter:
        query = query.filter(Scan.status == status_filter)

    pagination = query.order_by(Scan.scan_time.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return render_template(
        'history.html',
        scans=pagination.items,
        pagination=pagination,
        target_filter=target_filter,
        type_filter=type_filter,
        status_filter=status_filter,
    )


@dashboard_bp.route('/history/export/csv')
@login_required
def export_csv():
    """Export all scan history to CSV."""
    scans = Scan.query.options(joinedload(Scan.hosts)).order_by(Scan.scan_time.desc()).all()
    
    def generate():
        data = StringIO()
        writer = csv.writer(data)
        
        # Write header
        writer.writerow(['ID', 'Target', 'Scan Type', 'Status', 'Hosts Found', 'Duration (s)', 'Time'])
        yield data.getvalue()
        data.seek(0)
        data.truncate(0)
        
        # Write rows
        for scan in scans:
            writer.writerow([
                scan.id,
                scan.target,
                scan.scan_type,
                scan.status,
                len(scan.hosts),
                scan.duration_seconds,
                scan.scan_time.strftime('%Y-%m-%d %H:%M:%S') if scan.scan_time else ''
            ])
            yield data.getvalue()
            data.seek(0)
            data.truncate(0)

    response = Response(generate(), mimetype='text/csv')
    response.headers.set("Content-Disposition", "attachment", filename="scan_history.csv")
    return response


@dashboard_bp.route('/history/compare')
@login_required
def compare_scans():
    """Compare two scans and show the differences."""
    scan_ids = request.args.getlist('scan_ids')
    if len(scan_ids) != 2:
        flash("You must select exactly 2 scans to compare.", "warning")
        return redirect(url_for('dashboard.history'))
    
    # Get scans and ensure they exist
    try:
        scan1 = Scan.query.options(joinedload(Scan.hosts).joinedload(Host.ports)).get_or_404(int(scan_ids[0]))
        scan2 = Scan.query.options(joinedload(Scan.hosts).joinedload(Host.ports)).get_or_404(int(scan_ids[1]))
    except ValueError:
        flash("Invalid scan IDs.", "danger")
        return redirect(url_for('dashboard.history'))

    # Order them chronologically (older is base, newer is current)
    if scan1.scan_time > scan2.scan_time:
        scan1, scan2 = scan2, scan1

    # Diff Algorithm
    hosts1 = {h.ip_address: h for h in scan1.hosts}
    hosts2 = {h.ip_address: h for h in scan2.hosts}
    
    all_ips = set(hosts1.keys()).union(set(hosts2.keys()))
    
    diff = {
        'added_hosts': [],
        'removed_hosts': [],
        'common_hosts': []
    }
    
    for ip in all_ips:
        if ip not in hosts1:
            diff['added_hosts'].append(hosts2[ip])
        elif ip not in hosts2:
            diff['removed_hosts'].append(hosts1[ip])
        else:
            h1 = hosts1[ip]
            h2 = hosts2[ip]
            
            p1 = {p.port_number: p for p in h1.ports}
            p2 = {p.port_number: p for p in h2.ports}
            
            all_ports = set(p1.keys()).union(set(p2.keys()))
            
            port_diff = {
                'added': [],
                'removed': [],
                'changed': []
            }
            
            for p_num in all_ports:
                if p_num not in p1:
                    port_diff['added'].append(p2[p_num])
                elif p_num not in p2:
                    port_diff['removed'].append(p1[p_num])
                else:
                    if p1[p_num].port_state != p2[p_num].port_state:
                        port_diff['changed'].append((p1[p_num], p2[p_num]))
                        
            # Only add to common hosts if there's a difference in ports
            if port_diff['added'] or port_diff['removed'] or port_diff['changed']:
                diff['common_hosts'].append({
                    'ip': ip,
                    'hostname': h2.hostname or h1.hostname,
                    'port_diff': port_diff
                })
                
    return render_template('compare.html', scan1=scan1, scan2=scan2, diff=diff)


@dashboard_bp.route('/api/charts/ports')
@login_required
def chart_ports():
    """Return top 10 open ports for Chart.js."""
    results = db.session.query(
        Port.port_number, func.count(Port.id).label('count')
    ).filter_by(port_state='open').group_by(Port.port_number).order_by(func.count(Port.id).desc()).limit(10).all()
    
    data = {
        'labels': [f"Port {r.port_number}" for r in results],
        'counts': [r.count for r in results]
    }
    return jsonify(data)


@dashboard_bp.route('/api/charts/scans')
@login_required
def chart_scans():
    """Return scan counts per date for Chart.js."""
    results = db.session.query(
        func.date(Scan.scan_time).label('date'), func.count(Scan.id).label('count')
    ).group_by(func.date(Scan.scan_time)).order_by(func.date(Scan.scan_time)).limit(7).all()
    
    data = {
        'labels': [str(r.date) for r in results if r.date],
        'counts': [r.count for r in results if r.date]
    }
    return jsonify(data)
