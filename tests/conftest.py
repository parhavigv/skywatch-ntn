import os
import uuid
import pytest
import psycopg2
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

os.environ["DATABASE_URL"] = "postgresql://test:test@localhost:5432/skywatch_test"

from app.main import app
from app.api.deps import get_database, get_sync_database
from app.db.session import get_async_db, get_db

SYNC_URL  = "postgresql+psycopg2://test:test@localhost:5432/skywatch_test"
ASYNC_URL = "postgresql+asyncpg://test:test@localhost:5432/skywatch_test"

sync_engine       = create_engine(SYNC_URL, echo=False, pool_pre_ping=True)
async_engine      = create_async_engine(ASYNC_URL, echo=False, pool_pre_ping=True)
SyncSession       = sessionmaker(bind=sync_engine, autocommit=False, autoflush=False)
AsyncSessionMaker = async_sessionmaker(async_engine, expire_on_commit=False, class_=AsyncSession)

HEADERS = {"X-API-Key": "sw-admin-changeme-in-prod"}

VERTICALS = ["aviation", "maritime", "land", "iot", "defense"]
STATUSES  = ["online", "offline", "degraded"]


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


def _seed_devices(n: int = 500):
    """Insert n devices via raw psycopg2 so they exist before any test runs."""
    conn = psycopg2.connect(
        host="localhost", port=5432, dbname="skywatch_test",
        user="test", password="test"
    )
    try:
        cur = conn.cursor()
        # Check how many already exist
        cur.execute("SELECT COUNT(*) FROM devices")
        existing = cur.fetchone()[0]
        needed = n - existing
        if needed <= 0:
            return  # Already seeded

        rows = []
        for i in range(needed):
            rows.append((
                str(uuid.uuid4()),
                f"seed-device-{existing + i:05d}",
                VERTICALS[i % len(VERTICALS)],
                f"Location-{i}",
                STATUSES[i % len(STATUSES)],
                True,
            ))

        cur.executemany(
            """
            INSERT INTO devices (id, name, vertical, location, status, is_active)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (name) DO NOTHING
            """,
            rows,
        )
        conn.commit()
    finally:
        conn.close()


def _get_device(name):
    conn = psycopg2.connect(
        host="localhost", port=5432, dbname="skywatch_test",
        user="test", password="test"
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


# ── Seed BEFORE the session-scoped client is created ──────────────────────────
def pytest_sessionstart(session):
    """Called once before any tests run. Seeds the DB with 500 devices."""
    try:
        _seed_devices(500)
    except Exception as e:
        print(f"[conftest] WARNING: could not seed devices: {e}")


# ── Clean engine teardown — dispose via sync_engine only to avoid loop issues ──
def pytest_unconfigure(config):
    try:
        sync_engine.dispose()
    except Exception:
        pass
    # Dispose the async engine's underlying sync pool safely
    try:
        async_engine.sync_engine.dispose()
    except Exception:
        pass


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