from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from typing import List, Optional
from app.api.deps import get_database
from app.core.security import require_api_key, require_admin
from app.models.device import Device, VerticalType, DeviceStatus
from app.schemas.device import DeviceCreate, DeviceUpdate, DeviceResponse
from app.core.logging import logger

router = APIRouter()


@router.post(
    "/",
    response_model=DeviceResponse,
    status_code=201,
    summary="Register a new device",
)
async def create_device(
    payload: DeviceCreate,
    db: AsyncSession = Depends(get_database),
    _: str = Depends(require_api_key),
):
    result = await db.execute(
        select(Device).where(Device.name == payload.name)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail=f"Device '{payload.name}' already exists",
        )
    device = Device(**payload.model_dump())
    db.add(device)
    await db.flush()
    await db.refresh(device)
    logger.info("device_registered", device_id=device.id, name=device.name)
    return device


@router.get("/", response_model=List[DeviceResponse], summary="List all devices")
async def list_devices(
    vertical: Optional[VerticalType] = None,
    status: Optional[DeviceStatus] = None,
    is_active: Optional[bool] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_database),
    _: str = Depends(require_api_key),
):
    q = select(Device)
    if vertical:
        q = q.where(Device.vertical == vertical)
    if status:
        q = q.where(Device.status == status)
    if is_active is not None:
        q = q.where(Device.is_active == is_active)
    q = q.offset(skip).limit(limit)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/stats", summary="Fleet statistics")
async def fleet_stats(
    db: AsyncSession = Depends(get_database),
    _: str = Depends(require_api_key),
):
    total_result = await db.execute(select(func.count(Device.id)))
    total = total_result.scalar()

    vertical_result = await db.execute(
        select(Device.vertical, func.count(Device.id)).group_by(Device.vertical)
    )
    status_result = await db.execute(
        select(Device.status, func.count(Device.id)).group_by(Device.status)
    )
    return {
        "total_devices": total,
        "by_vertical": {v: c for v, c in vertical_result.all()},
        "by_status": {s: c for s, c in status_result.all()},
    }


@router.get(
    "/{device_id}",
    response_model=DeviceResponse,
    summary="Get device by ID",
)
async def get_device(
    device_id: str,
    db: AsyncSession = Depends(get_database),
    _: str = Depends(require_api_key),
):
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


@router.patch(
    "/{device_id}",
    response_model=DeviceResponse,
    summary="Update device",
)
async def update_device(
    device_id: str,
    payload: DeviceUpdate,
    db: AsyncSession = Depends(get_database),
    _: str = Depends(require_api_key),
):
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(device, field, value)
    await db.flush()
    await db.refresh(device)
    return device


@router.delete("/{device_id}", status_code=204, summary="Delete device")
async def delete_device(
    device_id: str,
    db: AsyncSession = Depends(get_database),
    role: str = Depends(require_admin),
):
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    await db.delete(device)
    logger.info("device_deleted", device_id=device_id, by_role=role)