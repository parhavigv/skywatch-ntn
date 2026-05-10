import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.session import get_db
from app.models.device import Device

TEST_DATABASE_URL = "postgresql://skywatch:skywatch123@localhost:5432/skywatch_db"
engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="module")
def sample_device(client):
    # Always query DB directly for the test device
    db = TestingSessionLocal()
    try:
        device = db.query(Device).filter(Device.name == "test-device-AVN-9999").first()
        if device:
            return {
                "id": device.id,
                "name": device.name,
                "vertical": device.vertical.value,
                "location": device.location,
                "status": device.status.value,
                "is_active": device.is_active,
                "created_at": str(device.created_at),
            }
    finally:
        db.close()

    # Not found — create it
    payload = {
        "name": "test-device-AVN-9999",
        "vertical": "aviation",
        "location": "Test Airport",
        "status": "online"
    }
    r = client.post("/api/v1/devices/", json=payload)
    assert r.status_code == 201, f"Failed to create device: {r.text}"
    return r.json()