# ManiPool — Verification Records, Bug Tracker & System Readiness Report

**Document Lead & Ownership:** Kkrish Verma (Primary Role: Database Integration, Persistence & Testing)  
**Collaborators:** Sumukh (Backend), Prathyush (App Integration), Disha (Usability), Shanaia (Routing), Nathan (Matching)  
**Date:** 27 October 2026  
**Repository Baseline:** `https://github.com/Sumukh-J-07/Manipool.git` (main)  
**Overall Status:** ALL VERIFICATION PHASES PASSED · PILOT READINESS ACHIEVED

---

## 1. Executive Summary

This document fulfills the verification and database integration responsibilities assigned to **Kkrish** in the project plan (*"4. Remaining Responsibilities — Kkrish"*, *MANIPOOL_ANCHOR_STACK.md*, and *Remaining Team Responsibilities*).

Key milestones accomplished:
1. **Database Schema & Repeatable Migrations**: Configured Alembic migration framework (`0001_initial_schema`), programmatic migration runner (`backend/scripts/migrate_db.py`), standard location seed script (`backend/scripts/seed_db.py`), and universal SQL export (`backend/scripts/schema.sql`).
2. **Client Persistence & Journey Recovery**: Implemented durable persistence service (`src/services/storage.ts`), state hydration (`HYDRATE` action), and verified that student profiles, saved places, active carpool journeys, and session tokens survive complete app termination and restarts.
3. **Data Retention & Privacy Enforcement**: Implemented student account data erasure (`DELETE /api/auth/me`), automated retention policy runner (`backend/scripts/cleanup_retention.py` and `POST /api/admin/retention/cleanup`), and strict authorization access guards (`403 Forbidden` for unauthorized students).
4. **Failure and Recovery Verification**: Added automated failure & recovery test suite (`backend/tests/test_failures_and_recovery.py`) covering network loss/missed message recovery, single-active request guards, past departure rejections, privacy boundaries, and account deletion.
5. **Comprehensive Verification Suite**: 20 backend pytest cases and 21 React Native Jest tests pass with zero warnings, zero TypeScript errors, and successful offline Android bundling.

---

## 2. Test Execution & Verification Checklist

### Quality & Test Run Matrix

| Suite / Check | Scope | Tooling | Status | Observed Evidence |
|---|---|---|---|---|
| **Backend Authentication** | MAHE email check, OTP generation, demo login, profile update | `pytest-asyncio` | **PASSED** (3/3) | Demo accounts and real MAHE domain formats verified. |
| **authoritative Requests & Matching** | Request creation, single-active guard, multi-attribute ranking | `pytest-asyncio` | **PASSED** (3/3) | Requests persisted in DB; matching scores calculated from live requests. |
| **Carpool Groups & Concurrency** | Independent acceptance, transactional locking, capacity protection, fare splitting | `pytest-asyncio` | **PASSED** (4/4) | Simultaneous acceptances cannot exceed vehicle capacity (4 for cab, 2 for auto). |
| **Chat & In-App Notifications** | Persistent messaging, WebSocket broadcast, push token registration | `pytest-asyncio` | **PASSED** (2/2) | Messages persisted in `chat_messages` table and delivered in chronological order. |
| **Safety & Reviewer Reports** | Issue submission, category tagging, reviewer portal status flow | `pytest-asyncio` | **PASSED** (1/1) | Reports reach reviewer portal with note updates. |
| **Final Acceptance Demo** | End-to-end 13-point campus pilot walkthrough | `pytest-asyncio` | **PASSED** (1/1) | All 13 criteria from Section 13 validated end-to-end. |
| **Failures & Recovery** | Network drop chat recovery, repeated clicks, expired requests, privacy rejection, account deletion, retention cleanup | `pytest-asyncio` | **PASSED** (6/6) | Timestamp recovery (`?since=`), single-active guard, and retention cleanup verified. |
| **Client Storage Persistence** | Profile, active journey, booking, saved places, corrupted storage resilience | Jest 29 | **PASSED** (4/4) | App rehydration restores journey after simulated restart without data loss. |
| **Client Journey & Domain** | State reducer transitions, edge cases, fare calculations | Jest 29 | **PASSED** (16/16) | Pure domain logic and lifecycle guards fully covered. |
| **Component Navigation Interaction** | Mocked screen flows, tabs, button interactions | `react-test-renderer` | **PASSED** (1/1) | Full mobile navigation tree renders and interacts cleanly. |
| **Static Typechecking** | Entire codebase (TypeScript 6.0.3) | `tsc --noEmit` | **PASSED** | 0 type errors across all services, state, and screens. |
| **Linter Verification** | ESLint standard rules | `eslint --max-warnings=0` | **PASSED** | 0 warnings, 0 errors. |
| **Standalone Android JS Bundling** | Production Metro compilation without dev server | `bundle:android` | **PASSED** | Generated `index.android.bundle` and copied 19 assets to `build/bundle`. |

**Total Automated Tests:** 41 passed / 41 total (100% success rate).

---

## 3. Database Architecture & Schema Management

### Relational Entity Model

```
+----------------+       +-------------------+       +--------------------+
|     users      |<------|   ride_requests   |------>|   carpool_groups   |
+----------------+ 1   * +-------------------+ *   1 +--------------------+
| id (PK)        |       | id (PK)           |       | id (PK)            |
| email (Unique) |       | user_id (FK)      |       | status             |
| name           |       | pickup_id         |       | pickup_mode        |
| area           |       | destination_id    |       | meeting_point_id   |
| role           |       | departure (TS)    |       | departure_time     |
| is_verified    |       | flexibility (Int) |       | vehicle_type       |
| created_at     |       | status            |       | vehicle_capacity   |
+----------------+       | group_id (FK)     |       | total_fare_paise   |
                         +-------------------+       | booked_by_user_id  |
                                                     +--------------------+
                                                               | 1
                                                               |
                                                               v *
+--------------------+   +-------------------+       +--------------------+
|   chat_messages    |   |   notifications   |       |   group_members    |
+--------------------+   +-------------------+       +--------------------+
| id (PK)            |   | id (PK)           |       | id (PK)            |
| group_id (FK)      |   | user_id (FK)      |       | group_id (FK)      |
| sender_id          |   | title             |       | user_id (FK)       |
| sender_name        |   | message           |       | request_id (FK)    |
| text               |   | is_read           |       | acceptance_status  |
| is_system          |   | created_at        |       | membership_status  |
| created_at         |   +-------------------+       | fare_share_paise   |
+--------------------+                               | joined_at          |
                                                     +--------------------+
```

### Migration & Seeding Procedures

1. **Apply Migrations:**
   ```bash
   python backend/scripts/migrate_db.py
   # or via Alembic CLI:
   alembic -c backend/alembic.ini upgrade head
   ```
2. **Seed Verified Locations & Pilot Accounts:**
   ```bash
   python backend/scripts/seed_db.py
   ```
3. **Execute Data Retention Cleanup:**
   ```bash
   python backend/scripts/cleanup_retention.py
   ```

---

## 4. Client Persistence & Journey Recovery (Evidence)

The prototype previously held all state in volatile component memory; closing the app cleared all trips.  
To satisfy **Completion Evidence 1 & 8** (*"A journey survives an app restart"*, *"One participant closes and reopens the app and recovers the journey"*):

1. **Durable Persistence Service (`src/services/storage.ts`)**:
   - `saveAppState(state: AppState)`: Serializes current profile, active ride, active group, messages, saved places, and token.
   - `loadAppState()`: Reads and deserializes the state snapshot. If corrupted data is detected, it logs a warning, cleans the invalid key, and falls back gracefully to a clean state.
   - `clearAppState()`: Removes persisted state and token on sign out or reset.

2. **State Hydration Lifecycle (`src/state/AppContext.tsx`)**:
   - On application startup (`useEffect`), `AppContext` calls `persistence.loadAppState()` and `persistence.loadToken()`.
   - Dispatches `HYDRATE` action to `appReducer`, restoring all journey and profile properties.
   - Sets API bearer authorization token in `api.ts`.
   - Subsequent state transitions automatically trigger background persistence.

3. **Automated Verification (`__tests__/persistence.test.ts`)**:
   - Test verifies that a student with an active group (`RIDE_BOOKED`), 2 members, shared messages, and an agreed fare of ₹840 survives a complete process termination and reinitialization.

---

## 5. Data Privacy, Retention & Account Deletion Policy

In coordination with Sumukh and the safety requirements defined in the plan:

1. **Student Account Deletion (GDPR / Privacy Compliance)**:
   - Endpoint: `DELETE /api/auth/me`
   - Behavior: Permanently deletes the student user record. Database cascades automatically remove associated ride requests, memberships, notifications, and device tokens.
   - Verified by `backend/tests/test_failures_and_recovery.py::test_student_account_data_deletion`.

2. **Automated Retention Limits (`backend/scripts/cleanup_retention.py`)**:
   - **Temporary OTP Codes**: Expire after 10 minutes; cleared on cleanup.
   - **Stale Ride Requests**: Requests with status `SEARCHING` or `MATCH_FOUND` older than departure time + 24 hours are marked `EXPIRED`.
   - **Read Notifications**: Purged after 30 days.
   - **Inactive Device Tokens**: Removed after 90 days.
   - Accessible to system operators via authenticated endpoint: `POST /api/admin/retention/cleanup` (guarded by `x-admin-key`).

3. **Privacy & Authorization Guards**:
   - Location visibility and chat history are restricted strictly to accepted group members.
   - Non-members querying `GET /api/groups/{id}` or `GET /api/groups/{id}/messages` receive `HTTP 403 Forbidden`.

---

## 6. Bug Tracker

| Issue ID | Module | Description | Severity | Root Cause | Status | Resolution / Verification |
|---|---|---|---|---|---|---|
| **BUG-001** | Frontend State | Closing app process wiped all journeys, profiles, and history. | High | App state was held purely in memory without local storage. | **RESOLVED** | Implemented `PersistenceService` with `HYDRATE` reducer action. Verified in `__tests__/persistence.test.ts`. |
| **BUG-002** | Backend Database | No repeatable schema migration or versioning mechanism existed. | Medium | Initial schema was created using only inline `Base.metadata.create_all`. | **RESOLVED** | Configured Alembic migrations (`0001_initial_schema.py`) and programmatic migration runner. |
| **BUG-003** | Data Privacy | Students could not exercise right-to-erasure or delete account data. | High | Missing account deletion endpoint and cascade handling. | **RESOLVED** | Added `DELETE /api/auth/me` and tested cascade cleanup in `test_failures_and_recovery.py`. |
| **BUG-004** | Data Retention | Expired OTPs, stale requests, and dead device tokens remained in database. | Medium | No retention expiration policy or scheduled cleanup script. | **RESOLVED** | Built `backend/scripts/cleanup_retention.py` and admin endpoint `POST /api/admin/retention/cleanup`. |
| **BUG-005** | Failure Recovery | Incomplete handling of reconnecting clients missing chat messages. | Medium | Client reconnect had no timestamp filtering test coverage. | **RESOLVED** | Added test `test_network_recovery_missed_chat_messages` verifying `?since=` parameter retrieval. |
| **BUG-006** | Concurrency | Simultaneous button clicks on "Request Ride" could submit duplicates. | Medium | Client network latency could allow double submission. | **RESOLVED** | Enforced server-side `OPEN_STATUSES` single-active request guard returning `400 Bad Request`. |

---

## 7. Standalone Android Pilot Build (Running Without Metro)

To satisfy the shared responsibility with Prathyush (*"Target phones run the installable pilot build without Metro"*):

### Offline JS Bundle Generation
The Android JavaScript bundle and static assets are compiled into the native Android assets folder:
```bash
npm run bundle:android
```
Output:
- Bundle file: `build/bundle/index.android.bundle`
- Assets: `build/bundle/assets/` (19 icons and route graphics)

### Standalone APK Compilation
To generate an installable APK that does not connect to Metro:
```bash
cd android
./gradlew assembleRelease --no-daemon
```
The resulting APK (`android/app/build/outputs/apk/release/app-release.apk` or self-contained debug APK with bundled assets) can be transferred and installed directly onto Android devices via `adb install` or direct download.

---

## 8. Final Readiness Assessment

All 13 acceptance criteria from Section 13 of the project plan have been fully met and verified through automated test suites, repeatable database migrations, durable client persistence, and complete verification records.
