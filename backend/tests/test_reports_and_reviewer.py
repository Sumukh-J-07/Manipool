import pytest
from httpx import AsyncClient

from backend.app.config import settings


async def get_token(client: AsyncClient, name: str, email: str) -> str:
    res = await client.post(
        "/api/auth/demo-login",
        json={"name": name, "email": email},
    )
    return res.json()["access_token"]


@pytest.mark.asyncio
async def test_issue_report_submission_and_reviewer_workflow(client: AsyncClient):
    student_token = await get_token(client, "StudentReporter", "studentrep@learner.manipal.edu")
    outsider_token = await get_token(client, "RegularStudent", "regular@learner.manipal.edu")

    student_headers = {"Authorization": f"Bearer {student_token}"}
    admin_headers = {"Authorization": f"Bearer {student_token}", "x-admin-key": settings.ADMIN_API_KEY}

    # 1. Student submits safety issue report
    rep_res = await client.post(
        "/api/reports",
        json={
            "text": "Rider did not show up at the agreed campus main gate meeting point.",
            "category": "NO_SHOW",
            "ride_id": "ride-12345",
        },
        headers=student_headers,
    )
    assert rep_res.status_code == 201
    rep_data = rep_res.json()
    report_id = rep_data["id"]
    assert rep_data["status"] == "OPEN"
    assert rep_data["category"] == "NO_SHOW"

    # 2. Student verifies report is in their personal list
    my_reports = await client.get("/api/reports", headers=student_headers)
    assert my_reports.status_code == 200
    assert len(my_reports.json()) >= 1

    # 3. Unauthorized student tries to access admin reports -> 403 Forbidden
    forbidden_res = await client.get(
        "/api/admin/reports",
        headers={"Authorization": f"Bearer {outsider_token}"},
    )
    assert forbidden_res.status_code == 403

    # 4. Reviewer accesses all reports using admin credentials
    admin_list = await client.get("/api/admin/reports", headers=admin_headers)
    assert admin_list.status_code == 200
    assert any(r["id"] == report_id for r in admin_list.json())

    # 5. Reviewer updates report status to RESOLVED with notes
    update_res = await client.patch(
        f"/api/admin/reports/{report_id}",
        json={
            "status": "RESOLVED",
            "reviewer_notes": "Contacted student. Apology issued and rider reliability metric adjusted.",
        },
        headers=admin_headers,
    )
    assert update_res.status_code == 200
    assert update_res.json()["status"] == "RESOLVED"
    assert update_res.json()["resolved_at"] is not None

    # 6. Verify student received resolution notification
    notifs = await client.get("/api/notifications", headers=student_headers)
    assert notifs.status_code == 200
    notif_titles = [n["title"] for n in notifs.json()]
    assert any("Report Update" in t for t in notif_titles)
