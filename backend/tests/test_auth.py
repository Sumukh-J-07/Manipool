import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_student_email_eligibility_enforcement(client: AsyncClient):
    # Non-MAHE email should be rejected
    res = await client.post(
        "/api/auth/register",
        json={
            "name": "Intruder",
            "email": "intruder@gmail.com",
            "area": "External",
        },
    )
    assert res.status_code == 400
    assert "MAHE student domains" in res.json()["detail"]

    # Valid MAHE learner email should succeed
    res = await client.post(
        "/api/auth/register",
        json={
            "name": "Prathyush",
            "email": "prathyush@learner.manipal.edu",
            "area": "MAHE Campus",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["access_token"]
    assert data["user"]["email"] == "prathyush@learner.manipal.edu"
    assert data["user"]["name"] == "Prathyush"


@pytest.mark.asyncio
async def test_otp_request_and_verify_flow(client: AsyncClient):
    # Request OTP for valid student
    res = await client.post(
        "/api/auth/request-otp",
        json={"email": "ananya@learner.manipal.edu"},
    )
    assert res.status_code == 200
    otp_code = res.json()["dev_otp_code"]
    assert len(otp_code) == 6

    # Verify with incorrect code fails
    bad_res = await client.post(
        "/api/auth/verify-otp",
        json={"email": "ananya@learner.manipal.edu", "code": "000000"},
    )
    assert bad_res.status_code == 400
    assert "Invalid verification code" in bad_res.json()["detail"]

    # Verify with correct code succeeds
    good_res = await client.post(
        "/api/auth/verify-otp",
        json={"email": "ananya@learner.manipal.edu", "code": otp_code},
    )
    assert good_res.status_code == 200
    data = good_res.json()
    assert data["access_token"]
    assert data["user"]["is_verified"] is True


@pytest.mark.asyncio
async def test_demo_login_and_profile(client: AsyncClient):
    # Demo login for Rahul
    res = await client.post(
        "/api/auth/demo-login",
        json={
            "name": "Rahul",
            "email": "rahul@learner.manipal.edu",
            "area": "Yelahanka area",
        },
    )
    assert res.status_code == 200
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Access current user profile
    me_res = await client.get("/api/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["name"] == "Rahul"

    # Update profile
    up_res = await client.put(
        "/api/auth/profile",
        json={"area": "New Yelahanka Town"},
        headers=headers,
    )
    assert up_res.status_code == 200
    assert up_res.json()["area"] == "New Yelahanka Town"
