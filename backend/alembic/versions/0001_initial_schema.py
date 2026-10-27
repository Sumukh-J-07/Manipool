"""Initial schema creation

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-10-27 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. users
    op.create_table(
        'users',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('area', sa.String(length=100), nullable=False, server_default='MAHE Campus'),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('otp_code', sa.String(length=10), nullable=True),
        sa.Column('otp_expires_at', sa.DateTime(), nullable=True),
        sa.Column('password_hash', sa.String(length=255), nullable=True),
        sa.Column('role', sa.String(length=20), nullable=False, server_default='student'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # 2. locations
    op.create_table(
        'locations',
        sa.Column('id', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('area', sa.String(length=100), nullable=False),
        sa.Column('kind', sa.String(length=30), nullable=False, server_default='campus'),
        sa.Column('corridor', sa.String(length=30), nullable=False, server_default='campus'),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_locations_name'), 'locations', ['name'], unique=False)
    op.create_index(op.f('ix_locations_corridor'), 'locations', ['corridor'], unique=False)

    # 3. carpool_groups
    op.create_table(
        'carpool_groups',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='WAITING_FOR_ACCEPTANCE'),
        sa.Column('pickup_mode', sa.String(length=20), nullable=False, server_default='common'),
        sa.Column('meeting_point_id', sa.String(length=50), nullable=False, server_default='campus'),
        sa.Column('meeting_point_name', sa.String(length=100), nullable=False, server_default='Campus Main Gate'),
        sa.Column('departure_time', sa.DateTime(), nullable=False),
        sa.Column('destination_id', sa.String(length=50), nullable=False),
        sa.Column('destination_name', sa.String(length=100), nullable=False),
        sa.Column('vehicle_type', sa.String(length=20), nullable=False, server_default='cab'),
        sa.Column('vehicle_capacity', sa.Integer(), nullable=False, server_default='4'),
        sa.Column('total_fare_paise', sa.Integer(), nullable=False, server_default='84000'),
        sa.Column('booked_by_user_id', sa.String(length=36), nullable=True),
        sa.Column('confirmed_at', sa.DateTime(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(), nullable=True),
        sa.Column('cancellation_reason', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['booked_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_carpool_groups_status'), 'carpool_groups', ['status'], unique=False)

    # 4. ride_requests
    op.create_table(
        'ride_requests',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('pickup_id', sa.String(length=50), nullable=False),
        sa.Column('pickup_name', sa.String(length=100), nullable=False),
        sa.Column('pickup_area', sa.String(length=100), nullable=False),
        sa.Column('pickup_lat', sa.Float(), nullable=True),
        sa.Column('pickup_lng', sa.Float(), nullable=True),
        sa.Column('destination_id', sa.String(length=50), nullable=False),
        sa.Column('destination_name', sa.String(length=100), nullable=False),
        sa.Column('destination_area', sa.String(length=100), nullable=False),
        sa.Column('destination_corridor', sa.String(length=50), nullable=False),
        sa.Column('destination_lat', sa.Float(), nullable=True),
        sa.Column('destination_lng', sa.Float(), nullable=True),
        sa.Column('departure', sa.DateTime(), nullable=False),
        sa.Column('flexibility', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='SEARCHING'),
        sa.Column('group_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['group_id'], ['carpool_groups.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ride_requests_departure'), 'ride_requests', ['departure'], unique=False)
    op.create_index(op.f('ix_ride_requests_group_id'), 'ride_requests', ['group_id'], unique=False)
    op.create_index(op.f('ix_ride_requests_status'), 'ride_requests', ['status'], unique=False)
    op.create_index(op.f('ix_ride_requests_user_id'), 'ride_requests', ['user_id'], unique=False)

    # 5. group_members
    op.create_table(
        'group_members',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('group_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('request_id', sa.String(length=36), nullable=True),
        sa.Column('acceptance_status', sa.String(length=20), nullable=False, server_default='PENDING'),
        sa.Column('membership_status', sa.String(length=20), nullable=False, server_default='ACTIVE'),
        sa.Column('fare_share_paise', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('joined_at', sa.DateTime(), nullable=False),
        sa.Column('accepted_at', sa.DateTime(), nullable=True),
        sa.Column('left_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['group_id'], ['carpool_groups.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['request_id'], ['ride_requests.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('group_id', 'user_id', name='uq_group_user')
    )
    op.create_index(op.f('ix_group_members_group_id'), 'group_members', ['group_id'], unique=False)
    op.create_index(op.f('ix_group_members_user_id'), 'group_members', ['user_id'], unique=False)

    # 6. chat_messages
    op.create_table(
        'chat_messages',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('group_id', sa.String(length=36), nullable=False),
        sa.Column('sender_id', sa.String(length=36), nullable=False),
        sa.Column('sender_name', sa.String(length=100), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('is_system', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['group_id'], ['carpool_groups.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_chat_messages_created_at'), 'chat_messages', ['created_at'], unique=False)
    op.create_index(op.f('ix_chat_messages_group_id'), 'chat_messages', ['group_id'], unique=False)
    op.create_index(op.f('ix_chat_messages_sender_id'), 'chat_messages', ['sender_id'], unique=False)

    # 7. notifications
    op.create_table(
        'notifications',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=150), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('group_id', sa.String(length=36), nullable=True),
        sa.Column('request_id', sa.String(length=36), nullable=True),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notifications_created_at'), 'notifications', ['created_at'], unique=False)
    op.create_index(op.f('ix_notifications_is_read'), 'notifications', ['is_read'], unique=False)
    op.create_index(op.f('ix_notifications_user_id'), 'notifications', ['user_id'], unique=False)

    # 8. device_tokens
    op.create_table(
        'device_tokens',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('token', sa.String(length=255), nullable=False),
        sa.Column('platform', sa.String(length=20), nullable=False, server_default='android'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'token', name='uq_user_device_token')
    )
    op.create_index(op.f('ix_device_tokens_token'), 'device_tokens', ['token'], unique=False)
    op.create_index(op.f('ix_device_tokens_user_id'), 'device_tokens', ['user_id'], unique=False)

    # 9. issue_reports
    op.create_table(
        'issue_reports',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('ride_id', sa.String(length=36), nullable=True),
        sa.Column('group_id', sa.String(length=36), nullable=True),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('category', sa.String(length=30), nullable=False, server_default='OTHER'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='OPEN'),
        sa.Column('reviewer_id', sa.String(length=36), nullable=True),
        sa.Column('reviewer_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_issue_reports_created_at'), 'issue_reports', ['created_at'], unique=False)
    op.create_index(op.f('ix_issue_reports_status'), 'issue_reports', ['status'], unique=False)
    op.create_index(op.f('ix_issue_reports_user_id'), 'issue_reports', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_table('issue_reports')
    op.drop_table('device_tokens')
    op.drop_table('notifications')
    op.drop_table('chat_messages')
    op.drop_table('group_members')
    op.drop_table('ride_requests')
    op.drop_table('carpool_groups')
    op.drop_table('locations')
    op.drop_table('users')
