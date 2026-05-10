from sqlalchemy import Column, String, Float, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import relationship
from app.db.base import Base
import uuid

class TelemetryRecord(Base):
    __tablename__ = "telemetry_records"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    device_id = Column(String, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    temperature = Column(Float, nullable=True)
    pressure = Column(Float, nullable=True)
    vibration = Column(Float, nullable=True)
    rpm = Column(Float, nullable=True)
    voltage = Column(Float, nullable=True)
    current = Column(Float, nullable=True)
    fuel_flow = Column(Float, nullable=True)
    load_factor = Column(Float, nullable=True)
    extra_metrics = Column(JSON, nullable=True)
    anomaly_score = Column(Float, default=0.0)

    device = relationship("Device", back_populates="telemetry_records")
