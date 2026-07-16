import logging
import os
from models import db, User, ScanHistory
from datetime import datetime

logger = logging.getLogger(__name__)

def init_db(app):
    """Initialize database and create tables"""
    with app.app_context():
        db.create_all()
        logger.info("Database tables created successfully!")
        
        # Create default admin if not exists
        create_default_admin()

def create_default_admin():
    """Create default admin user if it doesn't exist"""
    admin_email = 'admin@plagiarism.local'
    
    # Check if admin already exists
    existing_admin = User.query.filter_by(email=admin_email).first()
    if existing_admin:
        logger.info(f"Admin user already exists: {admin_email}")
        return existing_admin
    
    # Read default password from environment variable
    default_password = os.environ.get('DEFAULT_ADMIN_PASSWORD', 'Admin123!')
    
    # Create new admin
    admin = User(
        email=admin_email,
        name='Administrator',
        role='admin'
    )
    admin.set_password(default_password)
    
    db.session.add(admin)
    db.session.commit()
    
    logger.info("Default admin created!")
    logger.info(f"  Email: {admin_email}")
    logger.info("  Password: (set via DEFAULT_ADMIN_PASSWORD env variable)")
    logger.warning("  ⚠️  Please change the password after first login!")
    
    return admin

def get_db_stats():
    """Get database statistics"""
    total_users = User.query.count()
    admin_users = User.query.filter_by(role='admin').count()
    regular_users = User.query.filter_by(role='user').count()
    
    total_scans = ScanHistory.query.count()
    plagiarized_scans = ScanHistory.query.filter(ScanHistory.status.in_(['Plagiat', 'Warning'])).count()
    
    return {
        'total_users': total_users,
        'admin_users': admin_users,
        'regular_users': regular_users,
        'total_scans': total_scans,
        'plagiarized_scans': plagiarized_scans
    }
