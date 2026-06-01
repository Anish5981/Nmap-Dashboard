from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """Represents an admin user of the dashboard."""

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


class Scan(db.Model):
    """Represents a single Nmap scan execution."""

    __tablename__ = 'scans'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    target = db.Column(db.String(255), nullable=False)
    scan_type = db.Column(db.String(100), nullable=False)
    command_used = db.Column(db.String(500), nullable=False)
    scan_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    raw_xml_path = db.Column(db.String(500), nullable=False)
    duration_seconds = db.Column(db.Float, nullable=True)
    status = db.Column(
        db.Enum('running', 'completed', 'failed', 'timeout', name='scan_status'),
        nullable=False,
        default='running'
    )

    # Relationship
    hosts = db.relationship('Host', backref='scan', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'target': self.target,
            'scan_type': self.scan_type,
            'command_used': self.command_used,
            'scan_time': self.scan_time.strftime('%Y-%m-%d %H:%M:%S') if self.scan_time else None,
            'raw_xml_path': self.raw_xml_path,
            'duration_seconds': self.duration_seconds,
            'status': self.status,
            'host_count': len(self.hosts),
        }

    def __repr__(self):
        return f'<Scan {self.id}: {self.scan_type} on {self.target}>'


class Host(db.Model):
    """Represents a discovered host from a scan."""

    __tablename__ = 'hosts'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    scan_id = db.Column(db.Integer, db.ForeignKey('scans.id', ondelete='CASCADE'), nullable=False)
    ip_address = db.Column(db.String(45), nullable=False)
    hostname = db.Column(db.String(255), nullable=True)
    host_status = db.Column(
        db.Enum('up', 'down', name='host_status_enum'),
        nullable=False,
        default='up'
    )
    os_details = db.Column(db.Text, nullable=True)

    # Relationship
    ports = db.relationship('Port', backref='host', lazy=True, cascade='all, delete-orphan')

    def open_port_count(self):
        return sum(1 for p in self.ports if p.port_state == 'open')

    def to_dict(self):
        return {
            'id': self.id,
            'scan_id': self.scan_id,
            'ip_address': self.ip_address,
            'hostname': self.hostname,
            'host_status': self.host_status,
            'os_details': self.os_details,
            'open_ports': self.open_port_count(),
            'ports': [p.to_dict() for p in self.ports],
        }

    def __repr__(self):
        return f'<Host {self.ip_address} ({self.host_status})>'


class Port(db.Model):
    """Represents a port discovered on a host."""

    __tablename__ = 'ports'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    host_id = db.Column(db.Integer, db.ForeignKey('hosts.id', ondelete='CASCADE'), nullable=False)
    port_number = db.Column(db.Integer, nullable=False)
    protocol = db.Column(db.String(10), nullable=False, default='tcp')
    port_state = db.Column(
        db.Enum('open', 'closed', 'filtered', name='port_state_enum'),
        nullable=False,
        default='open'
    )
    service_name = db.Column(db.String(100), nullable=True)
    service_version = db.Column(db.String(255), nullable=True)
    script_output = db.Column(db.Text, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'host_id': self.host_id,
            'port_number': self.port_number,
            'protocol': self.protocol,
            'port_state': self.port_state,
            'service_name': self.service_name,
            'service_version': self.service_version,
            'script_output': self.script_output,
        }

    def __repr__(self):
        return f'<Port {self.port_number}/{self.protocol} ({self.port_state})>'
