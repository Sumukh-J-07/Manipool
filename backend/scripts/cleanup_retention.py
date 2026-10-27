"""ManiPool Data Retention & Privacy Policy Cleanup Script.

Enforces privacy and storage retention limits:
1. Clears expired OTP codes older than 10 minutes.
2. Marks unfulfilled ride requests past departure window (>24 hours) as EXPIRED.
3. Purges read notifications older than 30 days.
4. Cleans up inactive device push tokens older than 90 days.
"""
import asyncio
import os
import sys
from datetime import datetime, timedelta

# Add root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.database import AsyncSessionLocal
from backend.app.models.user import User
from backend.app.models.ride_request import RideRequest
from backend.app.models.notification import Notification, DeviceToken


async def run_retention_cleanup(session: AsyncSession | None = None) -> dict:
    now = datetime.utcnow()
    results = {
        "expired_otps_cleared": 0,
        "stale_requests_expired": 0,
        "old_notifications_purged": 0,
        "inactive_tokens_removed": 0,
    }

    async def _execute(s: AsyncSession):
        # 1. Clear expired OTP codes
        otp_query = update(User).where(
            User.otp_code.isnot(None),
            User.otp_expires_at < now,
        ).values(otp_code=None, otp_expires_at=None)
        otp_res = await s.execute(otp_query)
        results["expired_otps_cleared"] = otp_res.rowcount

        # 2. Expire stale open requests older than departure + 24 hours
        stale_cutoff = now - timedelta(hours=24)
        req_query = update(RideRequest).where(
            RideRequest.status.in_(["SEARCHING", "MATCH_FOUND"]),
            RideRequest.departure < stale_cutoff,
        ).values(status="EXPIRED")
        req_res = await s.execute(req_query)
        results["stale_requests_expired"] = req_res.rowcount

        # 3. Purge read notifications older than 30 days
        notif_cutoff = now - timedelta(days=30)
        notif_query = delete(Notification).where(
            Notification.is_read == True,
            Notification.created_at < notif_cutoff,
        )
        notif_res = await s.execute(notif_query)
        results["old_notifications_purged"] = notif_res.rowcount

        # 4. Remove inactive device tokens older than 90 days
        token_cutoff = now - timedelta(days=90)
        token_query = delete(DeviceToken).where(
            DeviceToken.updated_at < token_cutoff,
        )
        token_res = await s.execute(token_query)
        results["inactive_tokens_removed"] = token_res.rowcount

        await s.commit()

    if session is not None:
        await _execute(session)
    else:
        async with AsyncSessionLocal() as local_session:
            await _execute(local_session)

    print(f"Data retention cleanup completed at {now.isoformat()}:")
    for k, v in results.items():
        print(f" - {k}: {v}")
    return results


if __name__ == "__main__":
    asyncio.run(run_retention_cleanup())
