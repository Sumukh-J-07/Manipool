# ManiPool — Final Acceptance Demonstration Test Record

**Verification Date:** 26 October 2026  
**Backend Lead:** Sumukh  
**Test Suite:** `backend/tests/test_final_acceptance_demo.py` + `backend/tests/`  
**Execution Environment:** macOS, Python 3.14.6, FastAPI, pytest-asyncio  
**Overall Result:** ALL 13 ACCEPTANCE CRITERIA PASSED (14/14 Pytest Test Cases Passed)

---

## Acceptance Verification Results Table

| # | Acceptance Criterion | Verification Method | Status | Observed Evidence |
|---|---|---|---|---|
| **1** | **Three students sign in independently on separate devices** | Separate demo-login API calls for Prathyush, Ananya, and Rahul with distinct tokens | **PASSED** | 3 independent JWT bearer tokens generated with correct MAHE learner emails (`@learner.manipal.edu`). |
| **2** | **Each submits a real pickup, destination and departure window** | Prathyush (Campus $\to$ Airport, 18:45), Ananya (Gate $\to$ Airport, 18:55), Rahul (Yelahanka $\to$ Airport, 19:00) | **PASSED** | Requests created in DB with status `SEARCHING`/`MATCH_FOUND`; validated departure is in future and pickup $\ne$ destination. |
| **3** | **System proposes a compatible group using actual requests and route data** | Multi-attribute ranking on live DB requests: route overlap ($35\%$), detour ($25\%$), time window ($20\%$), destination ($15\%$), reliability ($5\%$) | **PASSED** | Prathyush's match search successfully finds Ananya and Rahul with high compatibility scores ($>0.8$), while excluding mismatched corridors. |
| **4** | **Each student accepts personally** | Separate requests to `POST /api/groups/{id}/accept` from each student's authenticated session | **PASSED** | Group transitions from `WAITING_FOR_ACCEPTANCE` to `GROUP_FORMED` only when all members accept personally. |
| **5** | **Group capacity remains correct, including simultaneous actions** | `asyncio.gather` concurrent join attempts by 2 riders for 1 remaining seat in auto/cab | **PASSED** | Atomic transaction lock (`group_transaction_lock`) admits exactly 1 rider (200 OK) and rejects the competing rider with `409 Conflict`. Capacity never exceeded. |
| **6** | **All participants see the same agreed pickup and departure details** | Pickup mode switched to Sequential; all 3 participants query group endpoint independently | **PASSED** | All 3 student sessions retrieve identical group state with `pickup_mode: "sequential"`. |
| **7** | **Participants exchange messages through shared chat** | Prathyush sends meeting message, Ananya replies; Rahul reads full persistent chat history | **PASSED** | Messages stored in `chat_messages` table and retrieved with correct sender attributes. |
| **8** | **One participant closes and reopens the app and recovers the journey** | Ananya's session re-authenticates with fresh token; active request and group ID queried | **PASSED** | Full active carpool journey, member statuses, and chat history restored seamlessly from backend. |
| **9** | **The group records an external booking and fare through agreed workflow** | Prathyush records shared cab booking (84,000 paise); capacity and vehicle rules checked | **PASSED** | Total fare split into exact equal shares (28,000 paise / ₹280 per rider); auto rejected if riders $> 2$. Status advances to `RIDE_BOOKED`. |
| **10** | **A cancellation produces consistent results for everyone** | One member leaves before departure; remaining members checked; secondary group cancelled when all leave | **PASSED** | Leaving member marked `LEFT`; remaining members remain `ACTIVE` and fare shares are automatically recalculated. Empty group transitions to `CANCELLED`. |
| **11** | **A network interruption produces understandable recovery behavior** | Client queries chat endpoint using `?since=` parameter timestamp after reconnection | **PASSED** | Missed messages retrieved in order; state transitions (`IN_PROGRESS` $\to$ `COMPLETED`) confirmed. |
| **12** | **The completed journey appears correctly in each participant’s history** | All 3 students query `GET /api/requests` after ride completion | **PASSED** | Journey archived with status `COMPLETED` in all participants' personal history records. |
| **13** | **An unrelated account cannot access the group’s private information** | Unrelated student (Sneha) attempts to view private group details and messages | **PASSED** | `HTTP 403 Forbidden` returned on both `GET /api/groups/{id}` and `GET /api/groups/{id}/messages`. Privacy rules strictly enforced. |

---

## Automated Test Run Output

```text
$ npm run backend:test

> MAHECarpool@1.0.0 backend:test
> backend/scripts/run_tests.sh

==========================================================
 Running ManiPool Backend Verification & Acceptance Tests 
==========================================================
============================= test session starts ==============================
platform darwin -- Python 3.14.6, pytest-9.1.1, pluggy-1.7.0 -- /Users/sumukhj/Documents/5th sem/CPI/Manipool/backend/.venv/bin/python3
cachedir: .pytest_cache
rootdir: /Users/sumukhj/Documents/5th sem/CPI/Manipool/backend
configfile: pytest.ini
plugins: asyncio-1.4.1, anyio-4.15.1
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=function, asyncio_default_test_loop_scope=function
collecting ... collected 14 items                                                             

tests/test_auth.py::test_student_email_eligibility_enforcement PASSED    [  7%]
tests/test_auth.py::test_otp_request_and_verify_flow PASSED              [ 14%]
tests/test_auth.py::test_demo_login_and_profile PASSED                   [ 21%]
tests/test_chat_and_notifications.py::test_chat_messaging_and_privacy_controls PASSED [ 28%]
tests/test_chat_and_notifications.py::test_notifications_and_device_tokens PASSED [ 35%]
tests/test_final_acceptance_demo.py::test_complete_13_point_acceptance_demonstration PASSED [ 42%]
tests/test_groups_and_concurrency.py::test_group_formation_and_independent_acceptance PASSED [ 50%]
tests/test_groups_and_concurrency.py::test_simultaneous_actions_and_capacity_protection PASSED [ 57%]
tests/test_groups_and_concurrency.py::test_booking_capacity_and_fare_splitting PASSED [ 64%]
tests/test_groups_and_concurrency.py::test_safe_member_exit_and_fare_recalculation PASSED [ 71%]
tests/test_reports_and_reviewer.py::test_issue_report_submission_and_reviewer_workflow PASSED [ 78%]
tests/test_requests_and_matching.py::test_ride_request_validation PASSED [ 85%]
tests/test_requests_and_matching.py::test_single_active_request_guard PASSED [ 92%]
tests/test_requests_and_matching.py::test_multi_user_matching_algorithm PASSED [100%]

============================== 14 passed in 0.96s ==============================
```

---

## Baseline React Native Verification

All existing frontend verification tests remain 100% passing without regression:

```text
$ npm run typecheck && npm run lint && npm test

> MAHECarpool@1.0.0 typecheck
> tsc --noEmit

> MAHECarpool@1.0.0 lint
> eslint . --max-warnings=0

> MAHECarpool@1.0.0 test
> jest

PASS __tests__/journey.test.ts
PASS __tests__/App.test.tsx

Test Suites: 2 passed, 2 total
Tests:       17 passed, 17 total
Snapshots:   0 total
Time:        3.071 s
```
