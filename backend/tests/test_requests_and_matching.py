from datetime import datetime, timedelta
import pytest
from httpx import AsyncClient


async def get_token(client: AsyncClient, name: str, email: str) -> str:
    res = await client.post(
        "/api/auth/demo-login",
        json={"name": name, "email": email},
    )
    return res.json()["access_token"]


@pytest.mark.asyncio
async def test_ride_request_validation(client: AsyncClient):
    token = await get_token(client, "Prathyush", "prathyush@learner.manipal.edu")
    headers = {"Authorization": f"Bearer {token}"}

    # Same pickup and destination rejected
    tomorrow = datetime.utcnow() + timedelta(days=1)
    res = await client.post(
        "/api/requests",
        json={
            "pickup_id": "campus",
            "destination_id": "campus",
            "departure": tomorrow.isoformat(),
            "flexibility": 30,
        },
        headers=headers,
    )
    assert res.status_code == 400
    assert "different" in res.json()["detail"]

    # Past departure rejected
    yesterday = datetime.utcnow() - timedelta(days=1)
    res = await client.post(
        "/api/requests",
        json={
            "pickup_id": "campus",
            "destination_id": "airport",
            "departure": yesterday.isoformat(),
            "flexibility": 30,
        },
        headers=headers,
    )
    assert res.status_code == 400
    assert "future" in res.json()["detail"]

    # Valid request created
    valid_res = await client.post(
        "/api/requests",
        json={
            "pickup_id": "campus",
            "destination_id": "airport",
            "departure": tomorrow.isoformat(),
            "flexibility": 30,
        },
        headers=headers,
    )
    assert valid_res.status_code == 201
    assert valid_res.json()["status"] in ("SEARCHING", "MATCH_FOUND")


@pytest.mark.asyncio
async def test_single_active_request_guard(client: AsyncClient):
    token = await get_token(client, "Ananya", "ananya@learner.manipal.edu")
    headers = {"Authorization": f"Bearer {token}"}
    tomorrow = datetime.utcnow() + timedelta(days=1)

    # First request
    res1 = await client.post(
        "/api/requests",
        json={
            "pickup_id": "campus",
            "destination_id": "airport",
            "departure": tomorrow.isoformat(),
            "flexibility": 30,
        },
        headers=headers,
    )
    assert res1.status_code == 201
    req_id = res1.json()["id"]

    # Second active request attempt rejected
    res2 = await client.post(
        "/api/requests",
        json={
            "pickup_id": "yelahanka",
            "destination_id": "airport",
            "departure": tomorrow.isoformat(),
            "flexibility": 15,
        },
        headers=headers,
    )
    assert res2.status_code == 400
    assert "already have an active request" in res2.json()["detail"]

    # Cancel first request
    del_res = await client.delete(f"/api/requests/{req_id}", headers=headers)
    assert del_res.status_code == 200

    # Now second request succeeds
    res3 = await client.post(
        "/api/requests",
        json={
            "pickup_id": "yelahanka",
            "destination_id": "airport",
            "departure": tomorrow.isoformat(),
            "flexibility": 15,
        },
        headers=headers,
    )
    assert res3.status_code == 201


@pytest.mark.asyncio
async def test_multi_user_matching_algorithm(client: AsyncClient):
    # Setup 4 distinct users with real requests
    token_a = await get_token(client, "Prathyush", "prathyush@learner.manipal.edu")
    token_b = await get_token(client, "Ananya", "ananya@learner.manipal.edu")
    token_c = await get_token(client, "Rahul", "rahul@learner.manipal.edu")
    token_d = await get_token(client, "Sneha", "sneha@learner.manipal.edu")

    base_time = datetime.utcnow() + timedelta(days=1)
    dep_a = base_time.replace(hour=18, minute=45, second=0, microsecond=0)
    dep_b = base_time.replace(hour=18, minute=55, second=0, microsecond=0)  # +10m, compatible
    dep_c = base_time.replace(hour=19, minute=0, second=0, microsecond=0)   # +15m, compatible
    dep_d = base_time.replace(hour=18, minute=45, second=0, microsecond=0)  # west corridor (railway)

    # User B: Campus gate -> Airport
    await client.post(
        "/api/requests",
        json={
            "pickup_id": "gate",
            "destination_id": "airport",
            "departure": dep_b.isoformat(),
            "flexibility": 15,
        },
        headers={"Authorization": f"Bearer {token_b}"},
    )

    # User C: Yelahanka -> Airport
    await client.post(
        "/api/requests",
        json={
            "pickup_id": "yelahanka",
            "destination_id": "airport",
            "departure": dep_c.isoformat(),
            "flexibility": 30,
        },
        headers={"Authorization": f"Bearer {token_c}"},
    )

    # User D: Campus -> Railway (different corridor)
    await client.post(
        "/api/requests",
        json={
            "pickup_id": "campus",
            "destination_id": "railway",
            "departure": dep_d.isoformat(),
            "flexibility": 30,
        },
        headers={"Authorization": f"Bearer {token_d}"},
    )

    # User A submits request: Campus -> Airport
    res_a = await client.post(
        "/api/requests",
        json={
            "pickup_id": "campus",
            "destination_id": "airport",
            "departure": dep_a.isoformat(),
            "flexibility": 30,
        },
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert res_a.status_code == 201
    data_a = res_a.json()
    assert data_a["status"] == "MATCH_FOUND"

    matches = data_a["matches"]
    assert len(matches) == 2  # Ananya and Rahul matched, Sneha excluded (different corridor)
    matched_names = [m["student"]["name"] for m in matches]
    assert "Ananya" in matched_names
    assert "Rahul" in matched_names
    assert "Sneha" not in matched_names

    # Verify score ranking and breakdown
    for m in matches:
        assert m["score"] > 0
        assert m["route_overlap"] >= 0.65
        assert m["detour_minutes"] <= 10
        assert m["pickup_km"] <= 2.0
