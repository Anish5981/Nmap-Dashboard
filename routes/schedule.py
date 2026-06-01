from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required
from models import db, ScheduledTask
from extensions import scheduler
from modules.scanner import SCAN_TYPES
import uuid

schedule_bp = Blueprint('schedule', __name__)


def scheduled_scan_job(target, scan_type_key, nmap_path, scans_dir, timeout):
    """The job function that APScheduler will run."""
    from app import create_app
    from routes.scan import _run_scan_thread
    from models import db, Scan
    from datetime import datetime

    app = create_app()
    with app.app_context():
        scan_config = SCAN_TYPES.get(scan_type_key)
        if not scan_config:
            return

        scan_record = Scan(
            target=target,
            scan_type=scan_config['name'] + ' (Scheduled)',
            command_used='',
            scan_time=datetime.utcnow(),
            raw_xml_path='',
            status='running',
        )
        db.session.add(scan_record)
        db.session.commit()

        # Run the scan synchronously inside this job thread
        _run_scan_thread(
            app, scan_record.id, target, scan_type_key, 
            nmap_path, scans_dir, timeout
        )


@schedule_bp.route('/schedules', methods=['GET'])
@login_required
def index():
    """List all scheduled tasks."""
    tasks = ScheduledTask.query.order_by(ScheduledTask.created_at.desc()).all()
    return render_template('schedule.html', tasks=tasks, scan_types=SCAN_TYPES)


@schedule_bp.route('/schedules/add', methods=['POST'])
@login_required
def add_schedule():
    """Create a new scheduled task."""
    target = request.form.get('target', '').strip()
    scan_type = request.form.get('scan_type')
    interval_minutes = request.form.get('interval')

    if not target or not scan_type or not interval_minutes:
        flash("All fields are required.", "danger")
        return redirect(url_for('schedule.index'))

    try:
        minutes = int(interval_minutes)
        if minutes < 1:
            raise ValueError
    except ValueError:
        flash("Interval must be a positive integer.", "danger")
        return redirect(url_for('schedule.index'))

    task_id = str(uuid.uuid4())
    
    new_task = ScheduledTask(
        id=task_id,
        target=target,
        scan_type=scan_type,
        schedule_type='interval',
        schedule_value=f"minutes={minutes}",
        is_active=True
    )
    db.session.add(new_task)
    db.session.commit()

    # Add to APScheduler
    app = current_app._get_current_object()
    scheduler.add_job(
        id=task_id,
        func=scheduled_scan_job,
        trigger='interval',
        minutes=minutes,
        args=[
            target, scan_type, 
            app.config['NMAP_PATH'], 
            app.config['SCANS_DIR'], 
            app.config['SCAN_TIMEOUT']
        ]
    )

    flash("Scheduled task created successfully.", "success")
    return redirect(url_for('schedule.index'))


@schedule_bp.route('/schedules/delete/<task_id>', methods=['POST'])
@login_required
def delete_schedule(task_id):
    """Delete a scheduled task."""
    task = ScheduledTask.query.get_or_404(task_id)
    
    try:
        scheduler.remove_job(task_id)
    except Exception:
        pass # Job might already be removed or missing

    db.session.delete(task)
    db.session.commit()

    flash("Scheduled task removed.", "success")
    return redirect(url_for('schedule.index'))
