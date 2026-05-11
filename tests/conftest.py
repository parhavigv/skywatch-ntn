import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.session import get_db, get_async_db
from app.models.device import Device

TEST_DATABASE_URL = "postgresql://skywatch:skywatch123@localhost:5432/skywatch_db"
engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

HEADERS = {"X-API-Key": "sw-admin-changeme-in-prod"}


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


async def override_get_async_db():
    db = TestingSessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_async_db] = override_get_async_db


@pytest.fixture(scope="module")
def client():
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


@pytest.fixture(scope="module")
def sample_device(client):
    db = TestingSessionLocal()
    try:
        device = db.query(Device).filter(
            Device.name == "test-device-AVN-9999"
        ).first()
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

    r = client.post(
        "/api/v1/devices/",
        json={"name": "test-device-AVN-9999", "vertical": "aviation",
              "location": "Test Airport", "status": "online"},
        headers=HEADERS,
    )
    assert r.status_code == 201, f"Failed: {r.text}"
    return r.json()