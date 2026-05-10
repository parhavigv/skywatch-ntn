from sqlalchemy import Column, String, Enum, Boolean, DateTime, func
from sqlalchemy.orm import relationship
from app.db.base import Base
import enum
import uuid

class VerticalType(str, enum.Enum):
    AVIATION = "aviation"
    MARINE = "marine"
    POWER_GRID = "power_grid"

class DeviceStatus(str, enum.Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    DEGRADED = "degraded"

class Device(Base):
    __tablename__ = "devices"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False, unique=True, index=True)
    vertical = Column(Enum(VerticalType), nullable=False, index=True)
    location = Column(String(100), nullable=False)
    status = Column(Enum(DeviceStatus), nullable=False, default=DeviceStatus.ONLINE)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    telemetry_records = relationship("TelemetryRecord", back_populates="device", cascade="all, delete-orphan")
