from models import db, User
from datetime import datetime

def init_db(app):
    """Initialize database and create tables"""
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")
        
        # Create default admin if not exists
        create_default_admin()

def create_default_admin():
    """Create default admin user if it doesn't exist"""
    admin_email = 'admin@plagiarism.local'
    
    # Check if admin already exists
    existing_admin = User.query.filter_by(email=admin_email).first()
    if existing_admin:
        print(f"Admin user already exists: {admin_email}")
        return existing_admin
    
    # Create new admin
    admin = User(
        email=admin_email,
        name='Administrator',
        role='admin'
    )
    admin.set_password('Admin123!')  # Default password
    
    db.session.add(admin)
    db.session.commit()
    
    print(f"Default admin created!")
    print(f"  Email: {admin_email}")
    print(f"  Password: Admin123!")
    print(f"  Please change the password after first login!")
    
    return admin

def get_db_stats():
    """Get database statistics"""
    total_users = User.query.count()
    admin_users = User.query.filter_by(role='admin').count()
    regular_users = User.query.filter_by(role='user').count()
    
    return {
        'total_users': total_users,
        'admin_users': admin_users,
        'regular_users': regular_users
    }
