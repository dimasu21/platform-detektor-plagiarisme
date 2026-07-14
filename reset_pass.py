from app import app
from models import db, User

with app.app_context():
    admin = User.query.filter_by(email='admin@plagiarism.local').first()
    if admin:
        admin.set_password('admin123')
        db.session.commit()
        print("Password updated successfully to admin123")
    else:
        print("Admin user not found")
