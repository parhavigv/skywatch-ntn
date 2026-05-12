import os, pytest, psycopg2
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

os.environ["DATABASE_URL"] = "postgresql://skywatch:skywatch123@localhost:5432/skywatch_db"

from app.main import app
from app.api.deps import get_database, get_sync_database
from app.db.session import get_async_db, get_db

SYNC_URL  = "postgresql+psycopg2://skywatch:skywatch123@localhost:5432/skywatch_db"
ASYNC_URL = "postgresql+asyncpg://skywatch:skywatch123@localhost:5432/skywatch_db"

sync_engine       = create_engine(SYNC_URL, echo=False, pool_pre_ping=True)
async_engine      = create_async_engine(ASYNC_URL, echo=False, pool_pre_ping=True)
SyncSession       = sessionmaker(bind=sync_engine, autocommit=False, autoflush=False)
AsyncSessionMaker = async_sessionmaker(async_engine, expire_on_commit=False, class_=AsyncSession)

HEADERS = {"X-API-Key": "sw-admin-changeme-in-prod"}


def override_get_db():
    db = SyncSession()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


async def override_get_async_db():
    async with AsyncSessionMaker() as session:
        async with session.begin():
            yield session


app.dependency_overrides[get_db]            = override_get_db
app.dependency_overrides[get_async_db]      = override_get_async_db
app.dependency_overrides[get_database]      = override_get_async_db
app.dependency_overrides[get_sync_database] = override_get_db


def pytest_unconfigure(config):
    try:
        import asyncio
        loop = asyncio.new_event_loop()
        loop.run_until_complete(async_engine.dispose())
        loop.close()
    except Exception:
        pass


def _get_device(name):
    conn = psycopg2.connect(
        host="localhost", port=5432, dbname="skywatch_db",
        user="skywatch", password="skywatch123"
    )
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, name, vertical, location, status, is_active, created_at "
            "FROM devices WHERE name = %s", (name,)
        )
        row = cur.fetchone()
        if row:
            return {
                "id":         row[0],
                "name":       row[1],
                "vertical":   row[2].lower(),
                "location":   row[3],
                "status":     row[4].lower(),
                "is_active":  row[5],
                "created_at": str(row[6]),
            }
        return None
    finally:
        conn.close()


@pytest.fixture(scope="session")
def client():
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


@pytest.fixture(scope="session")
def sample_device(client):
    d = _get_device("test-device-AVN-9999")
    if d:
        return d

    r = client.post(
        "/api/v1/devices/",
        json={
            "name":     "test-device-AVN-9999",
            "vertical": "aviation",
            "location": "Test Airport",
            "status":   "online",
        },
        headers=HEADERS,
    )

    if r.status_code == 201:
        return r.json()

    if r.status_code == 409:
        d = _get_device("test-device-AVN-9999")
        assert d is not None, "409 but device not in DB"
        return d

    pytest.fail(f"sample_device failed [{r.status_code}]: {r.text}")

