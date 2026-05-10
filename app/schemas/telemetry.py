from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class TelemetryIngest(BaseModel):
    device_id: str
    temperature: Optional[float] = None
    pressure: Optional[float] = None
    vibration: Optional[float] = None
    rpm: Optional[float] = None
    voltage: Optional[float] = None
    current: Optional[float] = None
    fuel_flow: Optional[float] = None
    load_factor: Optional[float] = None
    extra_metrics: Optional[Dict[str, Any]] = None

class TelemetryResponse(BaseModel):
    id: str
    device_id: str
    timestamp: datetime
    temperature: Optional[float]
    pressure: Optional[float]
    vibration: Optional[float]
    rpm: Optional[float]
    voltage: Optional[float]
    current: Optional[float]
    fuel_flow: Optional[float]
    load_factor: Optional[float]
    anomaly_score: float
    extra_metrics: Optional[Dict[str, Any]]

    model_config = {"from_attributes": True}

class TelemetryStats(BaseModel):
    device_id: str
    total_records: int
    avg_temperature: Optional[float]
    avg_vibration: Optional[float]
    avg_rpm: Optional[float]
    max_anomaly_score: float
