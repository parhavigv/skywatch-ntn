from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, timedelta
from app.api.deps import get_database
from app.models.device import Device
from app.models.telemetry import TelemetryRecord
from app.schemas.telemetry import TelemetryIngest, TelemetryResponse, TelemetryStats
import random

router = APIRouter()

def compute_anomaly_score(payload: TelemetryIngest) -> float:
    score = 0.0
    if payload.temperature and payload.temperature > 90:
        score += 0.4
    if payload.vibration and payload.vibration > 8.0:
        score += 0.3
    if payload.rpm and payload.rpm > 9000:
        score += 0.2
    if payload.voltage and (payload.voltage < 200 or payload.voltage > 260):
        score += 0.3
    return min(round(score, 2), 1.0)

@router.post("/ingest", response_model=TelemetryResponse, status_code=201, summary="Ingest telemetry from a device")
def ingest_telemetry(payload: TelemetryIngest, db: Session = Depends(get_database)):
    device = db.query(Device).filter(Device.id == payload.device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    anomaly_score = compute_anomaly_score(payload)
    record = TelemetryRecord(
        **payload.model_dump(),
        anomaly_score=anomaly_score,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

@router.post("/ingest/batch", summary="Batch ingest telemetry (up to 500 records)")
def ingest_batch(payloads: List[TelemetryIngest], db: Session = Depends(get_database)):
    if len(payloads) > 500:
        raise HTTPException(status_code=400, detail="Maximum 500 records per batch")
    device_ids = {p.device_id for p in payloads}
    existing_ids = {d.id for d in db.query(Device.id).filter(Device.id.in_(device_ids)).all()}
    missing = device_ids - existing_ids
    if missing:
        raise HTTPException(status_code=404, detail=f"Unknown device IDs: {missing}")
    records = [
        TelemetryRecord(**p.model_dump(), anomaly_score=compute_anomaly_score(p))
        for p in payloads
    ]
    db.bulk_save_objects(records)
    db.commit()
    return {"ingested": len(records), "status": "ok"}

@router.get("/device/{device_id}", response_model=List[TelemetryResponse], summary="Get telemetry for a device")
def get_device_telemetry(
    device_id: str,
    hours: int = Query(1, ge=1, le=168),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_database),
):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    since = datetime.utcnow() - timedelta(hours=hours)
    records = (
        db.query(TelemetryRecord)
        .filter(TelemetryRecord.device_id == device_id)
        .filter(TelemetryRecord.timestamp >= since)
        .order_by(TelemetryRecord.timestamp.desc())
        .limit(limit)
        .all()
    )
    return records

@router.get("/device/{device_id}/stats", response_model=TelemetryStats, summary="Telemetry statistics for a device")
def get_device_stats(device_id: str, db: Session = Depends(get_database)):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    stats = db.query(
        func.count(TelemetryRecord.id),
        func.avg(TelemetryRecord.temperature),
        func.avg(TelemetryRecord.vibration),
        func.avg(TelemetryRecord.rpm),
        func.max(TelemetryRecord.anomaly_score),
    ).filter(TelemetryRecord.device_id == device_id).one()
    return TelemetryStats(
        device_id=device_id,
        total_records=stats[0] or 0,
        avg_temperature=round(stats[1], 2) if stats[1] else None,
        avg_vibration=round(stats[2], 2) if stats[2] else None,
        avg_rpm=round(stats[3], 2) if stats[3] else None,
        max_anomaly_score=stats[4] or 0.0,
    )

@router.get("/anomalies", summary="Get high anomaly score records across fleet")
def get_anomalies(
    threshold: float = Query(0.5, ge=0.0, le=1.0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_database),
):
    records = (
        db.query(TelemetryRecord)
        .filter(TelemetryRecord.anomaly_score >= threshold)
        .order_by(TelemetryRecord.anomaly_score.desc())
        .limit(limit)
        .all()
    )
    return {"threshold": threshold, "count": len(records), "records": [
        {"id": r.id, "device_id": r.device_id, "anomaly_score": r.anomaly_score, "timestamp": r.timestamp}
        for r in records
    ]}
