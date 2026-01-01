"""Add OTP verification table

Revision ID: 614185049bbf
Revises: 7a0c0ccbc650
Create Date: 2025-01-XX XX:XX:XX.XXXXXX

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '614185049bbf'
down_revision = '7a0c0ccbc650'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('otp_verifications',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('email', sa.String(), nullable=False),
    sa.Column('otp_code', sa.String(length=6), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('is_verified', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_otp_verifications_id'), 'otp_verifications', ['id'], unique=False)
    op.create_index(op.f('ix_otp_verifications_email'), 'otp_verifications', ['email'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_otp_verifications_email'), table_name='otp_verifications')
    op.drop_index(op.f('ix_otp_verifications_id'), table_name='otp_verifications')
    op.drop_table('otp_verifications')

