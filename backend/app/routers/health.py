from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import settings
from backend.app.database import get_db
from backend.app.services.matching_service import LOCATIONS_COORDS

router = APIRouter(tags=["Health & Landmarks"])


@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    db_ok = False
    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    return {
        "status": "healthy" if db_ok else "degraded",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "database": "connected" if db_ok else "error",
    }


@router.get("/ready")
async def readiness_probe():
    return {"status": "ready"}


@router.get("/locations")
async def get_locations():
    return [
        {
            "id": loc_id,
            "name": data["name"],
            "area": data["area"],
            "corridor": data["corridor"],
            "lat": data.get("lat"),
            "lng": data.get("lng"),
        }
        for loc_id, data in LOCATIONS_COORDS.items()
    ]
