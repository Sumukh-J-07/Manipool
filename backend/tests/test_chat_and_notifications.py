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
async def test_chat_messaging_and_privacy_controls(client: AsyncClient):
    token_a = await get_token(client, "Prathyush", "prathyush@learner.manipal.edu")
    token_b = await get_token(client, "Ananya", "ananya@learner.manipal.edu")
    token_outsider = await get_token(client, "Outsider", "outsider@learner.manipal.edu")

    tomorrow = datetime.utcnow() + timedelta(days=1)
    dep = tomorrow.replace(hour=18, minute=45, second=0, microsecond=0)

    # Setup group
    ra = await client.post(
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

    # Student A posts a message
    msg_res = await client.post(
        f"/api/groups/{group_id}/messages",
        json={"text": "Hey Ananya! I will be near the main entrance."},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert msg_res.status_code == 201
    assert msg_res.json()["sender_name"] == "Prathyush"

    # Student B reads messages
    list_res = await client.get(
        f"/api/groups/{group_id}/messages",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert list_res.status_code == 200
    texts = [m["text"] for m in list_res.json()]
    assert "Hey Ananya! I will be near the main entrance." in texts

    # Outsider attempts to read messages -> MUST BE 403 FORBIDDEN
    outsider_read = await client.get(
        f"/api/groups/{group_id}/messages",
        headers={"Authorization": f"Bearer {token_outsider}"},
    )
    assert outsider_read.status_code == 403
    assert "not authorized" in outsider_read.json()["detail"].lower()

    # Outsider attempts to send a message -> MUST BE 403 FORBIDDEN
    outsider_send = await client.post(
        f"/api/groups/{group_id}/messages",
        json={"text": "Can I crash this ride?"},
        headers={"Authorization": f"Bearer {token_outsider}"},
    )
    assert outsider_send.status_code == 403


@pytest.mark.asyncio
async def test_notifications_and_device_tokens(client: AsyncClient):
    token_a = await get_token(client, "Nathan", "nathan@learner.manipal.edu")
    headers = {"Authorization": f"Bearer {token_a}"}

    # Register Android push token
    reg_res = await client.post(
        "/api/notifications/register-device",
        json={"token": "fcm-android-test-token-1234567890", "platform": "android"},
        headers=headers,
    )
    assert reg_res.status_code == 200

    # Check notification list
    notif_res = await client.get("/api/notifications", headers=headers)
    assert notif_res.status_code == 200
    assert isinstance(notif_res.json(), list)
