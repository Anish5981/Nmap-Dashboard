"""
Dashboard Routes

Handles the main dashboard homepage and scan history views.
"""

from flask import Blueprint, render_template, request
from models import db, Scan, Host, Port

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
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
