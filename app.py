"""
Nmap Scan Parser & Dashboard System
====================================
Flask application entry point.
"""

import os
from flask import Flask
from config import Config
from models import db


def create_app():
    """Flask application factory."""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize database
    db.init_app(app)

    # Ensure scans directory exists
    os.makedirs(app.config['SCANS_DIR'], exist_ok=True)

    # Register blueprints
    from routes.dashboard import dashboard_bp
    from routes.scan import scan_bp
    from routes.api import api_bp

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(scan_bp)
    app.register_blueprint(api_bp)

    # Create database tables
    with app.app_context():
        db.create_all()

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
