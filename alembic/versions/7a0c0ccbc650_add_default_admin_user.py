"""add_default_admin_user

Revision ID: 7a0c0ccbc650
Revises: c7e6ddb84463
Create Date: 2025-12-28 18:45:48.982048

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
import bcrypt
import uuid
from datetime import datetime, timezone


# revision identifiers, used by Alembic.
revision = '7a0c0ccbc650'
down_revision = 'c7e6ddb84463'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create default admin user if it doesn't exist"""
    # Hash the password using bcrypt (same as app/utils/security.py)
    admin_password = "Admin@123!"
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(admin_password.encode('utf-8'), salt).decode('utf-8')
    
    # Generate UUID for admin user
    admin_id = str(uuid.uuid4())
    admin_email = "admin@muckard.com"
    admin_name = "Admin User"
    current_time = datetime.now(timezone.utc)
    
    # Check if admin user already exists, if not create it
    connection = op.get_bind()
    result = connection.execute(
        text("SELECT id FROM users WHERE email = :email"),
        {"email": admin_email}
    )
    existing_admin = result.fetchone()
    
    if not existing_admin:
        # Insert admin user
        connection.execute(
            text("""
                INSERT INTO users (id, email, hashed_password, name, is_active, is_admin, created_at)
                VALUES (:id, :email, :hashed_password, :name, :is_active, :is_admin, :created_at)
            """),
            {
                "id": admin_id,
                "email": admin_email,
                "hashed_password": hashed_password,
                "name": admin_name,
                "is_active": True,
                "is_admin": True,
                "created_at": current_time
            }
        )


def downgrade() -> None:
    """Remove default admin user"""
    connection = op.get_bind()
    connection.execute(
        text("DELETE FROM users WHERE email = :email"),
        {"email": "admin@muckard.com"}
    )

