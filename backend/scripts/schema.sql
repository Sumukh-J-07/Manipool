-- ManiPool Database Schema
-- Compatible with SQLite 3.35+ and PostgreSQL 14+
-- Generated for MAHE Carpool Pilot

-- 1. Users Table
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(36) PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    area VARCHAR(100) NOT NULL DEFAULT 'MAHE Campus',
    is_verified BOOLEAN NOT NULL DEFAULT 0,
    otp_code VARCHAR(10),
    otp_expires_at TIMESTAMP,
    password_hash VARCHAR(255),
    role VARCHAR(20) NOT NULL DEFAULT 'student',
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_users_email ON users(email);

-- 2. Locations Table
CREATE TABLE IF NOT EXISTS locations (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    area VARCHAR(100) NOT NULL,
    kind VARCHAR(30) NOT NULL DEFAULT 'campus',
    corridor VARCHAR(30) NOT NULL DEFAULT 'campus',
    latitude FLOAT NOT NULL,
    longitude FLOAT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_locations_name ON locations(name);
CREATE INDEX IF NOT EXISTS ix_locations_corridor ON locations(corridor);

-- 3. Carpool Groups Table
CREATE TABLE IF NOT EXISTS carpool_groups (
    id VARCHAR(36) PRIMARY KEY,
    status VARCHAR(30) NOT NULL DEFAULT 'WAITING_FOR_ACCEPTANCE',
    pickup_mode VARCHAR(20) NOT NULL DEFAULT 'common',
    meeting_point_id VARCHAR(50) NOT NULL DEFAULT 'campus',
    meeting_point_name VARCHAR(100) NOT NULL DEFAULT 'Campus Main Gate',
    departure_time TIMESTAMP NOT NULL,
    destination_id VARCHAR(50) NOT NULL,
    destination_name VARCHAR(100) NOT NULL,
    vehicle_type VARCHAR(20) NOT NULL DEFAULT 'cab',
    vehicle_capacity INTEGER NOT NULL DEFAULT 4,
    total_fare_paise INTEGER NOT NULL DEFAULT 84000,
    booked_by_user_id VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL,
    confirmed_at TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    cancelled_at TIMESTAMP,
    cancellation_reason VARCHAR(255),
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_carpool_groups_status ON carpool_groups(status);

-- 4. Ride Requests Table
CREATE TABLE IF NOT EXISTS ride_requests (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    pickup_id VARCHAR(50) NOT NULL,
    pickup_name VARCHAR(100) NOT NULL,
    pickup_area VARCHAR(100) NOT NULL,
    pickup_lat FLOAT,
    pickup_lng FLOAT,
    destination_id VARCHAR(50) NOT NULL,
    destination_name VARCHAR(100) NOT NULL,
    destination_area VARCHAR(100) NOT NULL,
    destination_corridor VARCHAR(50) NOT NULL,
    destination_lat FLOAT,
    destination_lng FLOAT,
    departure TIMESTAMP NOT NULL,
    flexibility INTEGER NOT NULL DEFAULT 30,
    status VARCHAR(30) NOT NULL DEFAULT 'SEARCHING',
    group_id VARCHAR(36) REFERENCES carpool_groups(id) ON DELETE SET NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_ride_requests_user_id ON ride_requests(user_id);
CREATE INDEX IF NOT EXISTS ix_ride_requests_status ON ride_requests(status);
CREATE INDEX IF NOT EXISTS ix_ride_requests_group_id ON ride_requests(group_id);
CREATE INDEX IF NOT EXISTS ix_ride_requests_departure ON ride_requests(departure);

-- 5. Group Members Table
CREATE TABLE IF NOT EXISTS group_members (
    id VARCHAR(36) PRIMARY KEY,
    group_id VARCHAR(36) NOT NULL REFERENCES carpool_groups(id) ON DELETE CASCADE,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    request_id VARCHAR(36) REFERENCES ride_requests(id) ON DELETE SET NULL,
    acceptance_status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    membership_status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    fare_share_paise INTEGER NOT NULL DEFAULT 0,
    joined_at TIMESTAMP NOT NULL,
    accepted_at TIMESTAMP,
    left_at TIMESTAMP,
    CONSTRAINT uq_group_user UNIQUE (group_id, user_id)
);
CREATE INDEX IF NOT EXISTS ix_group_members_group_id ON group_members(group_id);
CREATE INDEX IF NOT EXISTS ix_group_members_user_id ON group_members(user_id);

-- 6. Chat Messages Table
CREATE TABLE IF NOT EXISTS chat_messages (
    id VARCHAR(36) PRIMARY KEY,
    group_id VARCHAR(36) NOT NULL REFERENCES carpool_groups(id) ON DELETE CASCADE,
    sender_id VARCHAR(36) NOT NULL,
    sender_name VARCHAR(100) NOT NULL,
    text TEXT NOT NULL,
    is_system BOOLEAN NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_chat_messages_group_id ON chat_messages(group_id);
CREATE INDEX IF NOT EXISTS ix_chat_messages_created_at ON chat_messages(created_at);

-- 7. In-App Notifications Table
CREATE TABLE IF NOT EXISTS notifications (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    title VARCHAR(150) NOT NULL,
    body TEXT NOT NULL,
    group_id VARCHAR(36),
    request_id VARCHAR(36),
    is_read BOOLEAN NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS ix_notifications_is_read ON notifications(is_read);

-- 8. Device Push Tokens Table
CREATE TABLE IF NOT EXISTS device_tokens (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(255) NOT NULL,
    platform VARCHAR(20) NOT NULL DEFAULT 'android',
    is_active BOOLEAN NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    CONSTRAINT uq_user_device_token UNIQUE (user_id, token)
);
CREATE INDEX IF NOT EXISTS ix_device_tokens_user_id ON device_tokens(user_id);

-- 9. Safety & Issue Reports Table
CREATE TABLE IF NOT EXISTS issue_reports (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    ride_id VARCHAR(36),
    group_id VARCHAR(36),
    text TEXT NOT NULL,
    category VARCHAR(30) NOT NULL DEFAULT 'OTHER',
    status VARCHAR(20) NOT NULL DEFAULT 'OPEN',
    reviewer_id VARCHAR(36),
    reviewer_notes TEXT,
    created_at TIMESTAMP NOT NULL,
    resolved_at TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_issue_reports_user_id ON issue_reports(user_id);
CREATE INDEX IF NOT EXISTS ix_issue_reports_status ON issue_reports(status);
