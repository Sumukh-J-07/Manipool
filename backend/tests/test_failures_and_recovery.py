import pytest
from datetime import datetime, timedelta
from httpx import AsyncClient
from backend.app.config import settings
from backend.scripts.cleanup_retention import run_retention_cleanup


@pytest.mark.asyncio
async def test_network_recovery_missed_chat_messages(client: AsyncClient):
    """Test failure recovery: client reconnects after network drop and recovers missed messages using timestamp."""
    # 1. Login Prathyush and Ananya
    login_p = await client.post(
        "/api/auth/demo-login",
        json={"name": "Prathyush", "email": "prathyush@learner.manipal.edu"},
    )
    token_p = login_p.json()["access_token"]

    login_a = await client.post(
        "/api/auth/demo-login",
        json={"name": "Ananya", "email": "ananya.sharma@learner.manipal.edu"},
    )
    token_a = login_a.json()["access_token"]

    # 2. Create ride requests and carpool group
    dep = (datetime.utcnow() + timedelta(hours=2)).isoformat()
    req_p = await client.post(
        "/api/requests",
        json={"pickup_id": "campus", "destination_id": "airport", "departure": dep, "flexibility": 30},
        headers={"Authorization": f"Bearer {token_p}"},
    )
    assert req_p.status_code == 201

    req_a = await client.post(
        "/api/requests",
        json={"pickup_id": "campus", "destination_id": "airport", "departure": dep, "flexibility": 30},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert req_a.status_code == 201

    grp = await client.post(
        "/api/groups",
        json={"candidate_request_ids": [req_a.json()["id"]], "pickup_mode": "common"},
        headers={"Authorization": f"Bearer {token_p}"},
    )
    assert grp.status_code == 201
    grp_id = grp.json()["id"]

    # 3. Both accept
    await client.post(f"/api/groups/{grp_id}/accept", headers={"Authorization": f"Bearer {token_p}"})
    await client.post(f"/api/groups/{grp_id}/accept", headers={"Authorization": f"Bearer {token_a}"})

    # 4. Prathyush sends initial message before Ananya drops off
    msg1 = await client.post(
        f"/api/groups/{grp_id}/messages",
        json={"text": "Meeting at Main Gate?"},
        headers={"Authorization": f"Bearer {token_p}"},
    )
    assert msg1.status_code == 201
    cutoff_time = msg1.json()["created_at"]

    # 5. Simulated Network drop: Ananya is offline while Prathyush sends 2 more messages
    msg2 = await client.post(
        f"/api/groups/{grp_id}/messages",
        json={"text": "Cab is arriving in 5 mins."},
        headers={"Authorization": f"Bearer {token_p}"},
    )
    msg3 = await client.post(
        f"/api/groups/{grp_id}/messages",
        json={"text": "I am wearing a blue jacket."},
        headers={"Authorization": f"Bearer {token_p}"},
    )
    assert msg2.status_code == 201
    assert msg3.status_code == 201

    # 6. Ananya reconnects and queries missed messages since cutoff_time
    missed_res = await client.get(
        f"/api/groups/{grp_id}/messages?since={cutoff_time}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert missed_res.status_code == 200
    missed_msgs = missed_res.json()
    assert len(missed_msgs) == 2
    assert missed_msgs[0]["text"] == "Cab is arriving in 5 mins."
    assert missed_msgs[1]["text"] == "I am wearing a blue jacket."


@pytest.mark.asyncio
async def test_repeated_button_press_and_idempotency(client: AsyncClient):
    """Test failure recovery: repeated button presses prevented by single-active guard."""
    login = await client.post(
        "/api/auth/demo-login",
        json={"name": "Rahul", "email": "rahul.verma@learner.manipal.edu"},
    )
    token = login.json()["access_token"]

    dep = (datetime.utcnow() + timedelta(hours=3)).isoformat()
    req_payload = {
        "pickup_id": "campus",
        "destination_id": "airport",
        "departure": dep,
        "flexibility": 30,
    }

    # First click: 201 Created
    res1 = await client.post(
        "/api/requests",
        json=req_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res1.status_code == 201

    # Second click immediately: Rejected with 400 Bad Request (single active guard)
    res2 = await client.post(
        "/api/requests",
        json=req_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res2.status_code == 400
    assert "already have an active request" in res2.json()["detail"]


@pytest.mark.asyncio
async def test_expired_request_and_past_departure(client: AsyncClient):
    """Test failure recovery: invalid past departure rejected."""
    login = await client.post(
        "/api/auth/demo-login",
        json={"name": "Sneha", "email": "sneha.rao@learner.manipal.edu"},
    )
    token = login.json()["access_token"]

    past_dep = (datetime.utcnow() - timedelta(minutes=15)).isoformat()
    res = await client.post(
        "/api/requests",
        json={
            "pickup_id": "campus",
            "destination_id": "airport",
            "departure": past_dep,
            "flexibility": 30,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 400
    assert "Choose a departure in the future" in res.json()["detail"]


@pytest.mark.asyncio
async def test_unauthorized_privacy_access_rejection(client: AsyncClient):
    """Test access rules: unrelated account is rejected with 403 Forbidden."""
    # User 1 creates group
    login1 = await client.post(
        "/api/auth/demo-login",
        json={"name": "Student A", "email": "student.a@learner.manipal.edu"},
    )
    token1 = login1.json()["access_token"]

    login_peer = await client.post(
        "/api/auth/demo-login",
        json={"name": "Peer", "email": "peer@learner.manipal.edu"},
    )
    token_peer = login_peer.json()["access_token"]

    dep = (datetime.utcnow() + timedelta(hours=2)).isoformat()
    req1 = await client.post(
        "/api/requests",
        json={"pickup_id": "campus", "destination_id": "airport", "departure": dep, "flexibility": 30},
        headers={"Authorization": f"Bearer {token1}"},
    )
    req_peer = await client.post(
        "/api/requests",
        json={"pickup_id": "campus", "destination_id": "airport", "departure": dep, "flexibility": 30},
        headers={"Authorization": f"Bearer {token_peer}"},
    )
    grp = await client.post(
        "/api/groups",
        json={"candidate_request_ids": [req_peer.json()["id"]], "pickup_mode": "common"},
        headers={"Authorization": f"Bearer {token1}"},
    )
    assert grp.status_code == 201
    grp_id = grp.json()["id"]

    # User 2 (unrelated intruder)
    login2 = await client.post(
        "/api/auth/demo-login",
        json={"name": "Intruder", "email": "intruder@learner.manipal.edu"},
    )
    token2 = login2.json()["access_token"]

    # Intruder tries to read group details
    get_res = await client.get(
        f"/api/groups/{grp_id}",
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert get_res.status_code == 403

    # Intruder tries to send message
    post_res = await client.post(
        f"/api/groups/{grp_id}/messages",
        json={"text": "Can I join?"},
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert post_res.status_code == 403


@pytest.mark.asyncio
async def test_student_account_data_deletion(client: AsyncClient):
    """Test GDPR/privacy student data deletion."""
    login = await client.post(
        "/api/auth/demo-login",
        json={"name": "To Delete", "email": "delete.me@learner.manipal.edu"},
    )
    token = login.json()["access_token"]

    # Verify profile exists
    me_res = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200

    # Delete account
    del_res = await client.delete("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert del_res.status_code == 200
    assert "deleted successfully" in del_res.json()["message"]

    # Verify subsequent calls fail with 401
    me_after = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_after.status_code == 401


@pytest.mark.asyncio
async def test_retention_policy_cleanup_endpoint(client: AsyncClient):
    """Test retention cleanup endpoint with admin authentication."""
    # Call without admin key: 403
    unauth = await client.post("/api/admin/retention/cleanup")
    assert unauth.status_code == 403

    # Call with valid admin key: 200
    res = await client.post(
        "/api/admin/retention/cleanup",
        headers={"x-admin-key": settings.ADMIN_API_KEY},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "success"
    assert "results" in res.json()
