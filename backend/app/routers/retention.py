from fastapi import APIRouter, Depends, Header, HTTPException, status
from backend.app.config import settings
from backend.scripts.cleanup_retention import run_retention_cleanup

from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.database import get_db

router = APIRouter(prefix="/admin/retention", tags=["Data Retention & Privacy"])


@router.post("/cleanup")
async def trigger_retention_cleanup(
    x_admin_key: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """Triggers data retention and privacy policy cleanup."""
    if not x_admin_key or x_admin_key != settings.ADMIN_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin key required to trigger retention cleanup.",
        )

    results = await run_retention_cleanup(session=db)
    return {
        "status": "success",
        "message": "Retention policy cleanup executed successfully.",
        "results": results,
    }
