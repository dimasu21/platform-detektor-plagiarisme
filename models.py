from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone

db = SQLAlchemy()

class User(UserMixin, db.Model):  # type: ignore[name-defined]
    """User model for authentication and profile management"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(200))
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), default='user')  # 'admin' or 'user'
    profile_picture = db.Column(db.String(200))  # URL or path to profile picture
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_login = db.Column(db.DateTime)
    
    def __init__(self, **kwargs):
        """Explicit init to satisfy type checker for keyword arguments."""
        super().__init__(**kwargs)
    
    def set_password(self, password):
        """Hash and set user password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if provided password matches hash"""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        """Check if user has admin role"""
        return self.role == 'admin'
    
    def __repr__(self):
        return f'<User {self.email}>'

class ScanHistory(db.Model):  # type: ignore[name-defined]
    """History of plagiarism scans"""
    __tablename__ = 'scan_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    suspect_filename = db.Column(db.String(255), nullable=False)
    method = db.Column(db.String(50), nullable=False)  # 'Single Check' or 'Batch Check'
    score = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False)  # 'Aman', 'Warning', 'Plagiat'
    
    # Relationship
    user = db.relationship('User', backref=db.backref('scans', lazy=True))
    
    def __init__(self, **kwargs):
        """Explicit init to satisfy type checker for keyword arguments."""
        super().__init__(**kwargs)
        
    def __repr__(self):
        return f'<ScanHistory {self.suspect_filename} ({self.score}%)>'
