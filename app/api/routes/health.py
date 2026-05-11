from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.api.deps import get_database
from app.core.config import settings
from app.core.logging import logger

router = APIRouter()


@router.get("/live", summary="Liveness probe")
async def liveness():
    return {"status": "alive", "app": settings.APP_NAME}


@router.get("/ready", summary="Readiness probe")
async def readiness(db: AsyncSession = Depends(get_database)):
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        from fastapi import HTTPException
        logger.error("readiness_check_failed", error=str(e))
        raise HTTPException(status_code=503, detail=f"Database not ready: {e}")


@router.get("/", summary="Health summary")
async def health_summary(db: AsyncSession = Depends(get_database)):
    try:
        await db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "disconnected"
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "database": db_status,
    }