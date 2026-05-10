from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.api.deps import get_database
from app.core.config import settings

router = APIRouter()

@router.get("/live", summary="Liveness probe")
def liveness():
    return {"status": "alive", "app": settings.APP_NAME}

@router.get("/ready", summary="Readiness probe")
def readiness(db: Session = Depends(get_database)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail=f"Database not ready: {str(e)}")

@router.get("/", summary="Health summary")
def health_summary(db: Session = Depends(get_database)):
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except:
        db_status = "disconnected"
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "database": db_status,
    }
