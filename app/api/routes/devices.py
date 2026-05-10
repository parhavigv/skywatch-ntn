from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from app.api.deps import get_database
from app.models.device import Device, VerticalType, DeviceStatus
from app.schemas.device import DeviceCreate, DeviceUpdate, DeviceResponse

router = APIRouter()

@router.post("/", response_model=DeviceResponse, status_code=201, summary="Register a new device")
def create_device(payload: DeviceCreate, db: Session = Depends(get_database)):
    existing = db.query(Device).filter(Device.name == payload.name).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Device '{payload.name}' already exists")
    device = Device(**payload.model_dump())
    db.add(device)
    db.commit()
    db.refresh(device)
    return device

@router.get("/", response_model=List[DeviceResponse], summary="List all devices")
def list_devices(
    vertical: Optional[VerticalType] = None,
    status: Optional[DeviceStatus] = None,
    is_active: Optional[bool] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_database),
):
    q = db.query(Device)
    if vertical:
        q = q.filter(Device.vertical == vertical)
    if status:
        q = q.filter(Device.status == status)
    if is_active is not None:
        q = q.filter(Device.is_active == is_active)
    return q.offset(skip).limit(limit).all()

@router.get("/stats", summary="Fleet statistics")
def fleet_stats(db: Session = Depends(get_database)):
    total = db.query(func.count(Device.id)).scalar()
    by_vertical = db.query(Device.vertical, func.count(Device.id)).group_by(Device.vertical).all()
    by_status = db.query(Device.status, func.count(Device.id)).group_by(Device.status).all()
    return {
        "total_devices": total,
        "by_vertical": {v: c for v, c in by_vertical},
        "by_status": {s: c for s, c in by_status},
    }

@router.get("/{device_id}", response_model=DeviceResponse, summary="Get device by ID")
def get_device(device_id: str, db: Session = Depends(get_database)):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device

@router.patch("/{device_id}", response_model=DeviceResponse, summary="Update device")
def update_device(device_id: str, payload: DeviceUpdate, db: Session = Depends(get_database)):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(device, field, value)
    db.commit()
    db.refresh(device)
    return device

@router.delete("/{device_id}", status_code=204, summary="Delete device")
def delete_device(device_id: str, db: Session = Depends(get_database)):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    db.delete(device)
    db.commit()
