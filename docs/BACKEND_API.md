# ManiPool Backend API Documentation

**Author & Ownership:** Sumukh (Primary Role: Backend Development)  
**Project:** ManiPool / MAHE Carpool  
**Framework:** FastAPI with Python 3.11+ / 3.14  
**Database:** SQLAlchemy (async) with SQLite (local development) and PostgreSQL / Supabase support

---

## 1. Overview & Architecture

The ManiPool backend service provides the shared multi-user server layer that connects independently running student devices into coordinated carpool journeys. It transforms the single-device frontend demonstration into a functioning multi-user system.

### Key Capabilities

1. **Authentication & Student Eligibility**:
   - Verification of MAHE email format (`@learner.manipal.edu` or `@manipal.edu`).
   - OTP generation and verification flow with 10-minute expiry.
   - Demo login endpoints for named pilot testers (`Prathyush`, `Ananya`, `Rahul`, `Sneha`, `Sumukh`).
   - Stateless JWT bearer token sessions (7-day validity).

2. **Authoritative Ride Request Lifecycle**:
   - Single-active request enforcement (prevents duplicate simultaneous open requests per student).
   - Validation of locations, departure window (must be future), and flexibility (0, 15, 30, 45 minutes).
   - Strict transition guards (`SEARCHING -> MATCH_FOUND -> WAITING_FOR_ACCEPTANCE -> GROUP_FORMED -> RIDE_BOOKED -> IN_PROGRESS -> COMPLETED`).

3. **Multi-User Matching Algorithm**:
   - Evaluates real, live ride requests stored in the database.
   - Time window overlap checking: $|dep_A - dep_B| \le flex_A + flex_B$.
   - Destination & corridor alignment (Campus, Airport, Central, North, West corridors).
   - Coordinate-based detour minutes and pickup distance evaluation ($\le 2.0$ km).
   - Weighted multi-attribute ranking:
     - Route overlap: 35%
     - Detour minimization: 25%
     - Departure time proximity: 20%
     - Destination match: 15%
     - Student reliability: 5%

4. **Group Formation & Safe Concurrency**:
   - Independent acceptance: each student reviews and accepts personally on their own device.
   - Per-group transaction locking (`group_transaction_lock`) preventing race conditions during simultaneous acceptances.
   - Strict vehicle capacity protection (Shared Cab: 4 passengers, Shared Auto: 2 passengers).
   - Competing requests beyond capacity are rejected with `HTTP 409 Conflict`.

5. **Pickup Agreement & External Booking Handoff**:
   - Common meeting point vs sequential pickup selection with participant notifications.
   - Departure delay coordination (+10 min).
   - External booking recorder with exact fare remainder splitting down to the paise.
   - Capacity enforcement: Booking an auto with $> 2$ passengers is rejected with `HTTP 400 Bad Request`.
   - Safe member exit: If a member leaves prior to trip start, the remaining group persists and fare shares are automatically recalculated.

6. **Shared Group Messaging & Live Sync**:
   - Persistent chat storage in database.
   - WebSocket endpoint (`/api/ws/chat/{group_id}`) for bidirectional realtime messages and system coordination broadcasts.
   - Timestamp-based recovery query (`?since=...`) ensuring missed messages are restored after network reconnects.

7. **Notification Events**:
   - In-app notification queue for match discovery, member acceptances, group formation, booking, delays, and cancellations.
   - Device push token registration endpoint (`/api/notifications/register-device`) supporting Android integration.

8. **Safety & Issue Report Handling**:
   - Student issue submission (`/api/reports`) for safety, no-shows, payments, or app defects.
   - Designated reviewer portal (`/api/admin/reports`) for tracking, status updates (`OPEN`, `UNDER_REVIEW`, `RESOLVED`, `DISMISSED`), reviewer notes, and automated student feedback.

---

## 2. API Endpoints Reference

### Authentication (`/api/auth`)

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/auth/register` | Register new student with password & MAHE email | No |
| `POST` | `/api/auth/request-otp` | Send 6-digit OTP to student email (returns `dev_otp_code` in dev mode) | No |
| `POST` | `/api/auth/verify-otp` | Verify OTP code and return JWT access token | No |
| `POST` | `/api/auth/login` | Login with email and password | No |
| `POST` | `/api/auth/demo-login` | Instant demo login for named pilot students | No |
| `GET` | `/api/auth/me` | Return currently authenticated student profile | Yes |
| `PUT` | `/api/auth/profile` | Update profile information (name, campus area) | Yes |

### Ride Requests (`/api/requests`)

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/requests` | Create real ride request (guarded by single-active check) | Yes |
| `GET` | `/api/requests` | List current student's requests (active and past) | Yes |
| `GET` | `/api/requests/{id}` | Get request details and live candidate matches | Yes |
| `DELETE` | `/api/requests/{id}` | Cancel an open ride request | Yes |
| `POST` | `/api/requests/{id}/rematch` | Rematch with updated flexibility window | Yes |

### Matching Engine (`/api/matching`)

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/api/matching/{request_id}` | Calculate live compatible match candidates from database | Yes |

### Carpool Groups (`/api/groups`)

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/groups` | Propose carpool group with candidate requests | Yes |
| `GET` | `/api/groups/{id}` | Get group details, active members, fare shares (access controlled) | Yes |
| `POST` | `/api/groups/{id}/accept` | Student accepts proposal (concurrency-locked, capacity-protected) | Yes |
| `POST` | `/api/groups/{id}/decline` | Student declines invitation | Yes |
| `POST` | `/api/groups/{id}/pickup-mode` | Switch pickup mode (`common` vs `sequential`) | Yes |
| `POST` | `/api/groups/{id}/delay` | Postpone departure time by X minutes | Yes |
| `POST` | `/api/groups/{id}/book` | Record external booking handoff and calculate exact fare split | Yes |
| `POST` | `/api/groups/{id}/start` | Mark journey `IN_PROGRESS` | Yes |
| `POST` | `/api/groups/{id}/complete` | Mark journey `COMPLETED` and archive into user history | Yes |
| `POST` | `/api/groups/{id}/leave` | Member leaves group; recalculates fare for remaining members | Yes |

### Group Messaging & Realtime (`/api/groups`, `/api/ws`)

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/api/groups/{id}/messages` | Get persistent message history (supports `?since=` for recovery) | Yes |
| `POST` | `/api/groups/{id}/messages` | Send custom chat message to group | Yes |
| `WS` | `/api/ws/chat/{group_id}?token=...` | Realtime bidirectional WebSocket connection | Token |

### Notifications (`/api/notifications`)

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/api/notifications` | Get in-app notification events for current user | Yes |
| `POST` | `/api/notifications/register-device` | Register device push token (Android FCM) | Yes |
| `PATCH` | `/api/notifications/{id}/read` | Mark notification event as read | Yes |

### Safety & Issue Reports (`/api/reports`, `/api/admin`)

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/reports` | Submit student issue report | Yes |
| `GET` | `/api/reports` | Get current student's submitted reports | Yes |
| `GET` | `/api/admin/reports` | Reviewer portal: list all reports (filter by status) | Reviewer / Admin Key |
| `PATCH` | `/api/admin/reports/{id}` | Reviewer portal: update report status & add notes | Reviewer / Admin Key |

### Health & Metadata (`/api`)

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/api/health` | Health check & database connection probe | No |
| `GET` | `/api/ready` | Readiness probe | No |
| `GET` | `/api/locations` | List standard MAHE Bengaluru landmarks and coordinates | No |

---

## 3. Running & Operating the Backend

### Prerequisites
- Python 3.11+
- virtualenv or uv

### Setup and Start
```bash
# From repository root
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Start backend server
python scripts/run_server.py
```
The server will start on `http://localhost:8000`.  
Interactive Swagger OpenAPI documentation is available at `http://localhost:8000/docs`.

### Running Tests
```bash
# Run pytest verification suite
./backend/scripts/run_tests.sh
# or from root
npm run backend:test
```

### Docker Deployment
```bash
cd backend
docker-compose up --build -d
```
