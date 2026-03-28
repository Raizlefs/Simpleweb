import os
from dotenv import load_dotenv
from api.index import app, db
from api.models import User

load_dotenv()

def init_db():
    with app.app_context():
        print("Creating database tables...")
        try:
            db.create_all()
        except Exception as e:
            print(f"Failed to create tables: {e}")
            return
        
        # Check if super admin already exists
        admin_username = os.environ.get('SUPER_ADMIN_USERNAME', 'admin')
        admin_password = os.environ.get('SUPER_ADMIN_PASSWORD', 'admin123')
        
        existing_admin = User.query.filter_by(username=admin_username).first()
        if not existing_admin:
            print(f"Creating super admin: {admin_username}")
            super_admin = User(username=admin_username, is_admin=True)
            super_admin.set_password(admin_password)
            db.session.add(super_admin)
            db.session.commit()
            print("Super admin created successfully!")
        else:
            print(f"Super admin '{admin_username}' already exists.")

if __name__ == "__main__":
    init_db()
