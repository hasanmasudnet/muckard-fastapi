#!/usr/bin/env python
"""Create a default admin user for testing"""
import sys
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.user import User
from app.utils.security import get_password_hash

def create_admin_user():
    """Create default admin user"""
    db: Session = SessionLocal()
    
    try:
        # Check if admin already exists
        admin = db.query(User).filter(User.email == "admin@muckard.com").first()
        if admin:
            print("Admin user already exists!")
            print(f"Email: {admin.email}")
            print(f"Name: {admin.name}")
            print(f"Is Admin: {admin.is_admin}")
            return
        
        # Create admin user
        admin = User(
            email="admin@muckard.com",
            name="Admin User",
            hashed_password=get_password_hash("Admin@123!"),  # Superadmin password
            is_admin=True,
            is_active=True
        )
        
        db.add(admin)
        db.commit()
        db.refresh(admin)
        
        print("=" * 50)
        print("Superadmin user created successfully!")
        print("=" * 50)
        print(f"Email: {admin.email}")
        print(f"Password: Admin@123!")
        print(f"Name: {admin.name}")
        print(f"Is Admin: {admin.is_admin}")
        print("=" * 50)
        
    except Exception as e:
        db.rollback()
        print(f"Error creating admin user: {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    create_admin_user()

