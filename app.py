"""
Nmap Scan Parser & Dashboard System
====================================
Flask application entry point.
"""

import os
from flask import Flask
from config import Config
from models import db, User
from flask_login import LoginManager


def create_app():
    """Flask application factory."""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize database
    db.init_app(app)

    # Initialize APScheduler
    app.config['SCHEDULER_API_ENABLED'] = True
    from extensions import scheduler
    scheduler.init_app(app)
    scheduler.start()

    # Ensure scans directory exists
    os.makedirs(app.config['SCANS_DIR'], exist_ok=True)

    # Initialize authentication
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'warning'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    from routes.dashboard import dashboard_bp
    from routes.scan import scan_bp
    from routes.api import api_bp
    from routes.auth import auth_bp
    from routes.schedule import schedule_bp

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(scan_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(schedule_bp)

    # Create database tables and default admin
    with app.app_context():
        db.create_all()
        
        # Create default admin user if none exists
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("Default admin user created (admin / admin123)")

        # Load Scheduled Tasks into APScheduler
        from models import ScheduledTask
        from routes.schedule import scheduled_scan_job
        tasks = ScheduledTask.query.filter_by(is_active=True).all()
        for task in tasks:
            # Parse minutes from "minutes=X"
            try:
                minutes = int(task.schedule_value.replace('minutes=', ''))
                scheduler.add_job(
                    id=task.id,
                    func=scheduled_scan_job,
                    trigger='interval',
                    minutes=minutes,
                    args=[
                        task.target, task.scan_type,
                        app.config['NMAP_PATH'],
                        app.config['SCANS_DIR'],
                        app.config['SCAN_TIMEOUT']
                    ],
                    replace_existing=True
                )
            except Exception as e:
                print(f"Error loading scheduled task {task.id}: {e}")

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
