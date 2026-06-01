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

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(scan_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(auth_bp)

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

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
