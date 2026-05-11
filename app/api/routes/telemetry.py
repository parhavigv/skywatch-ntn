from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from typing import List
from datetime import datetime, timedelta
from app.api.deps import get_database
from app.core.security import require_api_key
from app.core.anomaly import detector
from app.models.device import Device
from app.models.telemetry import TelemetryRecord
from app.schemas.telemetry import TelemetryIngest, TelemetryResponse, TelemetryStats
from app.core.logging import logger

router = APIRouter()


@router.post(
    "/ingest",
    response_model=TelemetryResponse,
    status_code=201,
    summary="Ingest single telemetry record",
)
async def ingest_telemetry(
    payload: TelemetryIngest,
    db: AsyncSession = Depends(get_database),
    _: str = Depends(require_api_key),
):
    result = await db.execute(
        select(Device).where(Device.id == payload.device_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Device not found")

    anomaly_score = detector.score(payload.device_id, payload.model_dump())
    if anomaly_score > 0.7:
        logger.warning(
            "high_anomaly_detected",
            device_id=payload.device_id,
            score=anomaly_score,
        )

    record = TelemetryRecord(**payload.model_dump(), anomaly_score=anomaly_score)
    db.add(record)
    await db.flush()
    await db.refresh(record)
    return record


@router.post("/ingest/batch", summary="Batch ingest telemetry (up to 500 records)")
async def ingest_batch(
    payloads: List[TelemetryIngest],
    db: AsyncSession = Depends(get_database),
    _: str = Depends(require_api_key),
):
    if len(payloads) > 500:
        raise HTTPException(
            status_code=400, detail="Maximum 500 records per batch"
        )

    device_ids = {p.device_id for p in payloads}
    result = await db.execute(
        select(Device.id).where(Device.id.in_(device_ids))
    )
    existing_ids = {row[0] for row in result.all()}
    missing = device_ids - existing_ids
    if missing:
        raise HTTPException(
            status_code=404, detail=f"Unknown device IDs: {missing}"
        )

    records = []
    high_anomaly_count = 0
    for p in payloads:
        score = detector.score(p.device_id, p.model_dump())
        if score > 0.7:
            high_anomaly_count += 1
        records.append(TelemetryRecord(**p.model_dump(), anomaly_score=score))

    db.add_all(records)
    await db.flush()

    if high_anomaly_count:
        logger.warning(
            "batch_anomalies_detected",
            count=high_anomaly_count,
            total=len(records),
        )

    return {"ingested": len(records), "status": "ok", "anomalies_flagged": high_anomaly_count}


@router.get(
    "/device/{device_id}",
    response_model=List[TelemetryResponse],
    summary="Get telemetry for a device",
)
async def get_device_telemetry(
    device_id: str,
    hours: int = Query(1, ge=1, le=168),
    limit: int = Query(100, ge=1, le=1000),
    min_anomaly: float = Query(0.0, ge=0.0, le=1.0),
    db: AsyncSession = Depends(get_database),
    _: str = Depends(require_api_key),
):
    result = await db.execute(select(Device).where(Device.id == device_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Device not found")

    since = datetime.utcnow() - timedelta(hours=hours)
    q = (
        select(TelemetryRecord)
        .where(TelemetryRecord.device_id == device_id)
        .where(TelemetryRecord.timestamp >= since)
        .where(TelemetryRecord.anomaly_score >= min_anomaly)
        .order_by(TelemetryRecord.timestamp.desc())
        .limit(limit)
    )
    result = await db.execute(q)
    return result.scalars().all()


@router.get(
    "/device/{device_id}/stats",
    response_model=TelemetryStats,
    summary="Aggregated stats for a device",
)
async def get_device_stats(
    device_id: str,
    db: AsyncSession = Depends(get_database),
    _: str = Depends(require_api_key),
):
    result = await db.execute(select(Device).where(Device.id == device_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Device not found")

    stats = await db.execute(
        select(
            func.count(TelemetryRecord.id),
            func.avg(TelemetryRecord.temperature),
            func.avg(TelemetryRecord.vibration),
            func.avg(TelemetryRecord.rpm),
            func.max(TelemetryRecord.anomaly_score),
        ).where(TelemetryRecord.device_id == device_id)
    )
    row = stats.one()
    return TelemetryStats(
        device_id=device_id,
        total_records=row[0] or 0,
        avg_temperature=round(row[1], 2) if row[1] else None,
        avg_vibration=round(row[2], 2) if row[2] else None,
        avg_rpm=round(row[3], 2) if row[3] else None,
        max_anomaly_score=row[4] or 0.0,
    )


@router.get("/device/{device_id}/ml-stats", summary="ML anomaly detector stats")
async def get_ml_stats(
    device_id: str,
    _: str = Depends(require_api_key),
):
    stats = detector.get_device_stats(device_id)
    if not stats:
        raise HTTPException(
            status_code=404,
            detail="No ML baseline built yet for this device",
        )
    return stats


@router.get("/anomalies", summary="Fleet-wide anomaly leaderboard")
async def get_anomalies(
    threshold: float = Query(0.5, ge=0.0, le=1.0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_database),
    _: str = Depends(require_api_key),
):
    result = await db.execute(
        select(TelemetryRecord)
        .where(TelemetryRecord.anomaly_score >= threshold)
        .order_by(TelemetryRecord.anomaly_score.desc())
        .limit(limit)
    )
    records = result.scalars().all()
    return {
        "threshold": threshold,
        "count": len(records),
        "records": [
            {
                "id": r.id,
                "device_id": r.device_id,
                "anomaly_score": r.anomaly_score,
                "timestamp": r.timestamp,
            }
            for r in records
        ],
    }