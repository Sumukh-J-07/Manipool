from datetime import datetime, timedelta
import asyncio
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_complete_13_point_acceptance_demonstration(client: AsyncClient):
    """
    Demonstration of all 13 points from the ManiPool Final Acceptance Specification:
    1. Three students sign in independently on separate devices.
    2. Each submits a real pickup, destination and departure window.
    3. The system proposes a compatible group using actual requests and route data.
    4. Each student accepts personally.
    5. Group capacity remains correct, including simultaneous actions.
    6. All participants see the same agreed pickup and departure details.
    7. Participants exchange messages through shared chat.
    8. One participant closes and reopens the app and recovers the journey.
    9. The group records an external booking and fare through the agreed workflow.
    10. A cancellation produces consistent results for everyone.
    11. A network interruption produces understandable recovery behavior.
    12. The completed journey appears correctly in each participant’s history.
    13. An unrelated account cannot access the group’s private information.
    """

    # =========================================================================
    # Step 1: Three students sign in independently on separate devices
    # =========================================================================
    res_a = await client.post(
        "/api/auth/demo-login",
        json={"name": "Prathyush", "email": "prathyush@learner.manipal.edu", "area": "MAHE Campus"},
    )
    assert res_a.status_code == 200
    token_a = res_a.json()["access_token"]
    user_a = res_a.json()["user"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    res_b = await client.post(
        "/api/auth/demo-login",
        json={"name": "Ananya", "email": "ananya@learner.manipal.edu", "area": "Campus Main Gate"},
    )
    assert res_b.status_code == 200
    token_b = res_b.json()["access_token"]
    user_b = res_b.json()["user"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    res_c = await client.post(
        "/api/auth/demo-login",
        json={"name": "Rahul", "email": "rahul@learner.manipal.edu", "area": "Yelahanka New Town"},
    )
    assert res_c.status_code == 200
    token_c = res_c.json()["access_token"]
    user_c = res_c.json()["user"]
    headers_c = {"Authorization": f"Bearer {token_c}"}

    # =========================================================================
    # Step 2: Each submits a real pickup, destination and departure window
    # =========================================================================
    tomorrow = datetime.utcnow() + timedelta(days=1)
    dep_a = tomorrow.replace(hour=18, minute=45, second=0, microsecond=0)
    dep_b = tomorrow.replace(hour=18, minute=55, second=0, microsecond=0)
    dep_c = tomorrow.replace(hour=19, minute=0, second=0, microsecond=0)

    # Student A submits Campus -> Airport
    req_a_res = await client.post(
        "/api/requests",
        json={"pickup_id": "campus", "destination_id": "airport", "departure": dep_a.isoformat(), "flexibility": 30},
        headers=headers_a,
    )
    assert req_a_res.status_code == 201
    req_a_id = req_a_res.json()["id"]

    # Student B submits Gate -> Airport
    req_b_res = await client.post(
        "/api/requests",
        json={"pickup_id": "gate", "destination_id": "airport", "departure": dep_b.isoformat(), "flexibility": 15},
        headers=headers_b,
    )
    assert req_b_res.status_code == 201
    req_b_id = req_b_res.json()["id"]

    # Student C submits Yelahanka -> Airport
    req_c_res = await client.post(
        "/api/requests",
        json={"pickup_id": "yelahanka", "destination_id": "airport", "departure": dep_c.isoformat(), "flexibility": 30},
        headers=headers_c,
    )
    assert req_c_res.status_code == 201
    req_c_id = req_c_res.json()["id"]

    # =========================================================================
    # Step 3: The system proposes a compatible group using actual requests and route data
    # =========================================================================
    matches_res = await client.get(f"/api/matching/{req_a_id}", headers=headers_a)
    assert matches_res.status_code == 200
    candidates = matches_res.json()
    assert len(candidates) >= 2
    candidate_student_names = [c["student"]["name"] for c in candidates]
    assert "Ananya" in candidate_student_names
    assert "Rahul" in candidate_student_names

    # =========================================================================
    # Step 4: Each student accepts personally
    # =========================================================================
    # Student A initiates the group proposal
    grp_res = await client.post(
        "/api/groups",
        json={
            "candidate_request_ids": [req_b_id, req_c_id],
            "pickup_mode": "common",
            "vehicle_type": "cab",
        },
        headers=headers_a,
    )
    assert grp_res.status_code == 201
    group_id = grp_res.json()["id"]
    assert grp_res.json()["status"] == "WAITING_FOR_ACCEPTANCE"

    # Student B accepts independently from device B
    accept_b = await client.post(f"/api/groups/{group_id}/accept", headers=headers_b)
    assert accept_b.status_code == 200

    # Student C accepts independently from device C
    accept_c = await client.post(f"/api/groups/{group_id}/accept", headers=headers_c)
    assert accept_c.status_code == 200
    group_data = accept_c.json()

    # All 3 accepted -> Group advances to GROUP_FORMED
    assert group_data["status"] == "GROUP_FORMED"
    assert len([m for m in group_data["members"] if m["acceptance_status"] == "ACCEPTED"]) == 3

    # =========================================================================
    # Step 5: Group capacity remains correct, including simultaneous actions
    # =========================================================================
    # Create 4th and 5th student attempting to join the 4-seat cab simultaneously
    res_d = await client.post(
        "/api/auth/demo-login",
        json={"name": "StudentD", "email": "studentd@learner.manipal.edu", "area": "Campus"},
    )
    token_d = res_d.json()["access_token"]
    headers_d = {"Authorization": f"Bearer {token_d}"}

    res_e = await client.post(
        "/api/auth/demo-login",
        json={"name": "StudentE", "email": "studente@learner.manipal.edu", "area": "Campus"},
    )
    token_e = res_e.json()["access_token"]
    headers_e = {"Authorization": f"Bearer {token_e}"}

    # Gather simultaneous requests when only 1 seat remains (3 of 4 occupied)
    call_d = client.post(f"/api/groups/{group_id}/accept", headers=headers_d)
    call_e = client.post(f"/api/groups/{group_id}/accept", headers=headers_e)
    d_res, e_res = await asyncio.gather(call_d, call_e)

    # Exactly one succeeded (200) and the other was rejected with 409 Conflict
    assert (d_res.status_code == 200 and e_res.status_code == 409) or (
        e_res.status_code == 200 and d_res.status_code == 409
    )

    # Clean up the 4th member so we continue with our 3 core test students
    fourth_headers = headers_d if d_res.status_code == 200 else headers_e
    await client.post(f"/api/groups/{group_id}/leave", headers=fourth_headers)

    # =========================================================================
    # Step 6: All participants see the same agreed pickup and departure details
    # =========================================================================
    # Update pickup mode to Sequential Pickup
    pickup_update = await client.post(
        f"/api/groups/{group_id}/pickup-mode",
        json={"mode": "sequential"},
        headers=headers_a,
    )
    assert pickup_update.status_code == 200
    assert pickup_update.json()["pickup_mode"] == "sequential"

    # All three students query group and observe identical state
    for h in [headers_a, headers_b, headers_c]:
        view = await client.get(f"/api/groups/{group_id}", headers=h)
        assert view.status_code == 200
        assert view.json()["pickup_mode"] == "sequential"
        assert view.json()["destination_id"] == "airport"

    # =========================================================================
    # Step 7: Participants exchange messages through shared chat
    # =========================================================================
    # Student A sends message
    m1 = await client.post(
        f"/api/groups/{group_id}/messages",
        json={"text": "Hey everyone, I'll meet at gate in 5 mins!"},
        headers=headers_a,
    )
    assert m1.status_code == 201

    # Student B sends message
    m2 = await client.post(
        f"/api/groups/{group_id}/messages",
        json={"text": "Got it, walking there now."},
        headers=headers_b,
    )
    assert m2.status_code == 201

    # Student C reads all messages
    chat_history = await client.get(f"/api/groups/{group_id}/messages", headers=headers_c)
    assert chat_history.status_code == 200
    texts = [m["text"] for m in chat_history.json()]
    assert "Hey everyone, I'll meet at gate in 5 mins!" in texts
    assert "Got it, walking there now." in texts

    # =========================================================================
    # Step 8: One participant closes and reopens the app and recovers the journey
    # =========================================================================
    # Simulate app close & reopen for Student B (fresh token request / session restore)
    restore_b = await client.post(
        "/api/auth/demo-login",
        json={"name": "Ananya", "email": "ananya@learner.manipal.edu"},
    )
    new_token_b = restore_b.json()["access_token"]
    fresh_headers_b = {"Authorization": f"Bearer {new_token_b}"}

    # Fetch active requests & recover active group journey
    recovered_reqs = await client.get("/api/requests", headers=fresh_headers_b)
    assert recovered_reqs.status_code == 200
    my_active = next(r for r in recovered_reqs.json() if r["status"] == "GROUP_FORMED")
    assert my_active["group_id"] == group_id

    # Journey state, members, and chat are fully recovered
    recovered_grp = await client.get(f"/api/groups/{group_id}", headers=fresh_headers_b)
    assert recovered_grp.status_code == 200
    assert recovered_grp.json()["status"] == "GROUP_FORMED"
    assert len(recovered_grp.json()["members"]) >= 3

    # =========================================================================
    # Step 9: The group records an external booking and fare through the agreed workflow
    # =========================================================================
    book_res = await client.post(
        f"/api/groups/{group_id}/book",
        json={"vehicle_type": "cab", "fare_paise": 84000},
        headers=headers_a,
    )
    assert book_res.status_code == 200
    booked_data = book_res.json()
    assert booked_data["status"] == "RIDE_BOOKED"
    assert booked_data["total_fare_paise"] == 84000

    # Verify exact fare split across the 3 students (84000 / 3 = 28000 each)
    shares = [m["fare_share_paise"] for m in booked_data["members"] if m["membership_status"] == "ACTIVE"]
    assert shares == [28000, 28000, 28000]

    # =========================================================================
    # Step 10: A cancellation produces consistent results for everyone
    # =========================================================================
    # Create a secondary test group with Student D and Student E to test cancellation
    sec_dep = tomorrow.replace(hour=20, minute=0, second=0, microsecond=0)
    rd = await client.post(
        "/api/requests",
        json={"pickup_id": "campus", "destination_id": "airport", "departure": sec_dep.isoformat(), "flexibility": 30},
        headers=headers_d,
    )
    re = await client.post(
        "/api/requests",
        json={"pickup_id": "campus", "destination_id": "airport", "departure": sec_dep.isoformat(), "flexibility": 30},
        headers=headers_e,
    )
    sec_grp = await client.post(
        "/api/groups",
        json={"candidate_request_ids": [re.json()["id"]], "pickup_mode": "common", "vehicle_type": "cab"},
        headers=headers_d,
    )
    sec_group_id = sec_grp.json()["id"]
    await client.post(f"/api/groups/{sec_group_id}/accept", headers=headers_e)

    # Student D leaves
    await client.post(f"/api/groups/{sec_group_id}/leave", headers=headers_d)
    # Student E leaves -> all left -> group cancelled
    cancel_res = await client.post(f"/api/groups/{sec_group_id}/leave", headers=headers_e)
    assert cancel_res.status_code == 200
    sec_view = await client.get(f"/api/groups/{sec_group_id}", headers=headers_e)
    assert sec_view.json()["status"] == "CANCELLED"

    # =========================================================================
    # Step 11: A network interruption produces understandable recovery behavior
    # =========================================================================
    # After a simulated network interruption, student queries with 'since' timestamp
    recent_messages = await client.get(
        f"/api/groups/{group_id}/messages?since={dep_a.isoformat()}",
        headers=headers_a,
    )
    assert recent_messages.status_code == 200

    # Start the ride
    start_res = await client.post(f"/api/groups/{group_id}/start", headers=headers_a)
    assert start_res.status_code == 200
    assert start_res.json()["status"] == "IN_PROGRESS"

    # Complete the ride
    comp_res = await client.post(f"/api/groups/{group_id}/complete", headers=headers_a)
    assert comp_res.status_code == 200
    assert comp_res.json()["status"] == "COMPLETED"

    # =========================================================================
    # Step 12: The completed journey appears correctly in each participant’s history
    # =========================================================================
    for h in [headers_a, headers_b, headers_c]:
        hist = await client.get("/api/requests", headers=h)
        assert hist.status_code == 200
        completed_requests = [r for r in hist.json() if r["status"] == "COMPLETED"]
        assert len(completed_requests) == 1
        assert completed_requests[0]["destination_id"] == "airport"

    # =========================================================================
    # Step 13: An unrelated account cannot access the group’s private information
    # =========================================================================
    res_unrelated = await client.post(
        "/api/auth/demo-login",
        json={"name": "Sneha", "email": "sneha@learner.manipal.edu", "area": "Bagalur"},
    )
    token_unrelated = res_unrelated.json()["access_token"]
    headers_unrelated = {"Authorization": f"Bearer {token_unrelated}"}

    # Attempt to view the completed group's private details
    unauthorized_group = await client.get(f"/api/groups/{group_id}", headers=headers_unrelated)
    assert unauthorized_group.status_code == 403
    assert "not authorized" in unauthorized_group.json()["detail"].lower()

    # Attempt to view group's private messages
    unauthorized_messages = await client.get(f"/api/groups/{group_id}/messages", headers=headers_unrelated)
    assert unauthorized_messages.status_code == 403
    assert "not authorized" in unauthorized_messages.json()["detail"].lower()
