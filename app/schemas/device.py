from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.device import VerticalType, DeviceStatus

class DeviceCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    vertical: VerticalType
    location: str = Field(..., min_length=2, max_length=100)
    status: DeviceStatus = DeviceStatus.ONLINE

class DeviceUpdate(BaseModel):
    status: Optional[DeviceStatus] = None
    location: Optional[str] = None
    is_active: Optional[bool] = None

class DeviceResponse(BaseModel):
    id: str
    name: str
    vertical: VerticalType
    location: str
    status: DeviceStatus
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
