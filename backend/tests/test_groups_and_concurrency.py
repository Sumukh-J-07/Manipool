import asyncio
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
async def test_group_formation_and_independent_acceptance(client: AsyncClient):
    token_a = await get_token(client, "Prathyush", "prathyush@learner.manipal.edu")
    token_b = await get_token(client, "Ananya", "ananya@learner.manipal.edu")

    tomorrow = datetime.utcnow() + timedelta(days=1)
    dep = tomorrow.replace(hour=18, minute=45, second=0, microsecond=0)

    # Student B request
    res_b = await client.post(
        "/api/requests",
        json={
            "pickup_id": "campus",
            "destination_id": "airport",
            "departure": dep.isoformat(),
            "flexibility": 30,
        },
        headers={"Authorization": f"Bearer {token_b}"},
    )
    req_b_id = res_b.json()["id"]

    # Student A request
    res_a = await client.post(
        "/api/requests",
        json={
            "pickup_id": "campus",
            "destination_id": "airport",
            "departure": dep.isoformat(),
            "flexibility": 30,
        },
        headers={"Authorization": f"Bearer {token_a}"},
    )
    req_a_id = res_a.json()["id"]

    # Student A proposes group with Student B
    group_res = await client.post(
        "/api/groups",
        json={
            "candidate_request_ids": [req_b_id],
            "pickup_mode": "common",
            "vehicle_type": "cab",
        },
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert group_res.status_code == 201
    group_data = group_res.json()
    group_id = group_data["id"]
    assert group_data["status"] == "WAITING_FOR_ACCEPTANCE"

    # Verify Student A is ACCEPTED and Student B is PENDING
    members = {m["name"]: m["acceptance_status"] for m in group_data["members"]}
    assert members["Prathyush"] == "ACCEPTED"
    assert members["Ananya"] == "PENDING"

    # Student B independently signs in and accepts
    accept_res = await client.post(
        f"/api/groups/{group_id}/accept",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert accept_res.status_code == 200
    updated_group = accept_res.json()
    assert updated_group["status"] == "GROUP_FORMED"

    # Both are now accepted
    for m in updated_group["members"]:
        assert m["acceptance_status"] == "ACCEPTED"


@pytest.mark.asyncio
async def test_simultaneous_actions_and_capacity_protection(client: AsyncClient):
    """
    Test competing concurrent acceptances when only 1 seat remains in a 2-seat Auto.
    Capacity MUST NOT be exceeded; competing request must receive 409 Conflict.
    """
    token_a = await get_token(client, "StudentA", "studenta@learner.manipal.edu")
    token_b = await get_token(client, "StudentB", "studentb@learner.manipal.edu")
    token_c = await get_token(client, "StudentC", "studentc@learner.manipal.edu")

    tomorrow = datetime.utcnow() + timedelta(days=1)
    dep = tomorrow.replace(hour=18, minute=45, second=0, microsecond=0)

    # Student A creates request
    res_a = await client.post(
        "/api/requests",
        json={
            "pickup_id": "campus",
            "destination_id": "airport",
            "departure": dep.isoformat(),
            "flexibility": 30,
        },
        headers={"Authorization": f"Bearer {token_a}"},
    )

    # Student B creates request
    res_b = await client.post(
        "/api/requests",
        json={
            "pickup_id": "campus",
            "destination_id": "airport",
            "departure": dep.isoformat(),
            "flexibility": 30,
        },
        headers={"Authorization": f"Bearer {token_b}"},
    )
    req_b_id = res_b.json()["id"]

    # Student C creates request
    await client.post(
        "/api/requests",
        json={
            "pickup_id": "campus",
            "destination_id": "airport",
            "departure": dep.isoformat(),
            "flexibility": 30,
        },
        headers={"Authorization": f"Bearer {token_c}"},
    )

    # Student A creates an Auto group (capacity: 2 seats)
    group_res = await client.post(
        "/api/groups",
        json={
            "candidate_request_ids": [req_b_id],
            "pickup_mode": "common",
            "vehicle_type": "auto",
        },
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert group_res.status_code == 201
    group_id = group_res.json()["id"]
    assert group_res.json()["vehicle_capacity"] == 2

    # Now Student B and Student C attempt to accept/join concurrently!
    # One slot is already taken by Student A. Only 1 slot remains.
    res_b_task = client.post(
        f"/api/groups/{group_id}/accept",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    res_c_task = client.post(
        f"/api/groups/{group_id}/accept",
        headers={"Authorization": f"Bearer {token_c}"},
    )

    resp_b, resp_c = await asyncio.gather(res_b_task, res_c_task)

    statuses = [resp_b.status_code, resp_c.status_code]
    assert 200 in statuses
    assert 409 in statuses  # One was rejected due to capacity limit!

    # Verify group detail has exactly 2 members and capacity is strictly respected
    final_res = await client.get(
        f"/api/groups/{group_id}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    final_members = [
        m for m in final_res.json()["members"]
        if m["membership_status"] == "ACTIVE" and m["acceptance_status"] == "ACCEPTED"
    ]
    assert len(final_members) == 2


@pytest.mark.asyncio
async def test_booking_capacity_and_fare_splitting(client: AsyncClient):
    token_a = await get_token(client, "Rider1", "rider1@learner.manipal.edu")
    token_b = await get_token(client, "Rider2", "rider2@learner.manipal.edu")
    token_c = await get_token(client, "Rider3", "rider3@learner.manipal.edu")

    tomorrow = datetime.utcnow() + timedelta(days=1)
    dep = tomorrow.replace(hour=18, minute=45, second=0, microsecond=0)

    # Create 3 requests
    await client.post(
        "/api/requests",
        json={"pickup_id": "campus", "destination_id": "airport", "departure": dep.isoformat(), "flexibility": 30},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    r2 = await client.post(
        "/api/requests",
        json={"pickup_id": "campus", "destination_id": "airport", "departure": dep.isoformat(), "flexibility": 30},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    r3 = await client.post(
        "/api/requests",
        json={"pickup_id": "campus", "destination_id": "airport", "departure": dep.isoformat(), "flexibility": 30},
        headers={"Authorization": f"Bearer {token_c}"},
    )

    # Form 3-rider group
    grp = await client.post(
        "/api/groups",
        json={"candidate_request_ids": [r2.json()["id"], r3.json()["id"]], "pickup_mode": "common", "vehicle_type": "cab"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    group_id = grp.json()["id"]

    await client.post(f"/api/groups/{group_id}/accept", headers={"Authorization": f"Bearer {token_b}"})
    await client.post(f"/api/groups/{group_id}/accept", headers={"Authorization": f"Bearer {token_c}"})

    # Try booking Auto with 3 riders -> MUST BE REJECTED (capacity = 2)
    auto_res = await client.post(
        f"/api/groups/{group_id}/book",
        json={"vehicle_type": "auto"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert auto_res.status_code == 400
    assert "capacity" in auto_res.json()["detail"].lower()

    # Book Cab with 3 riders -> SUCCEEDS and splits fare exactly
    cab_res = await client.post(
        f"/api/groups/{group_id}/book",
        json={"vehicle_type": "cab", "fare_paise": 84000},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert cab_res.status_code == 200
    cab_data = cab_res.json()
    assert cab_data["status"] == "RIDE_BOOKED"

    # Fare splitting: 84000 / 3 = 28000 paise (₹280) each
    shares = [m["fare_share_paise"] for m in cab_data["members"]]
    assert shares == [28000, 28000, 28000]
    assert sum(shares) == 84000


@pytest.mark.asyncio
async def test_safe_member_exit_and_fare_recalculation(client: AsyncClient):
    token_a = await get_token(client, "RiderA", "ridera@learner.manipal.edu")
    token_b = await get_token(client, "RiderB", "riderb@learner.manipal.edu")

    tomorrow = datetime.utcnow() + timedelta(days=1)
    dep = tomorrow.replace(hour=18, minute=45, second=0, microsecond=0)

    await client.post(
        "/api/requests",
        json={"pickup_id": "campus", "destination_id": "airport", "departure": dep.isoformat(), "flexibility": 30},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    rb = await client.post(
        "/api/requests",
        json={"pickup_id": "campus", "destination_id": "airport", "departure": dep.isoformat(), "flexibility": 30},
        headers={"Authorization": f"Bearer {token_b}"},
    )

    grp = await client.post(
        "/api/groups",
        json={"candidate_request_ids": [rb.json()["id"]], "pickup_mode": "common", "vehicle_type": "cab"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    group_id = grp.json()["id"]
    await client.post(f"/api/groups/{group_id}/accept", headers={"Authorization": f"Bearer {token_b}"})

    # Book ride: 84000 paise split by 2 = 42000 paise each
    await client.post(
        f"/api/groups/{group_id}/book",
        json={"vehicle_type": "cab", "fare_paise": 84000},
        headers={"Authorization": f"Bearer {token_a}"},
    )

    # Rider B leaves the group before start
    leave_res = await client.post(
        f"/api/groups/{group_id}/leave",
        json={"reason": "Schedule conflict"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert leave_res.status_code == 200
    assert leave_res.json()["remaining_members_count"] == 1

    # Check updated group: Rider A is remaining, fare share recalculated to 84000 paise
    grp_res = await client.get(
        f"/api/groups/{group_id}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    members = grp_res.json()["members"]
    rider_a_mem = next(m for m in members if m["name"] == "RiderA")
    rider_b_mem = next(m for m in members if m["name"] == "RiderB")

    assert rider_a_mem["membership_status"] == "ACTIVE"
    assert rider_a_mem["fare_share_paise"] == 84000  # Recalculated for sole remaining passenger
    assert rider_b_mem["membership_status"] == "LEFT"
