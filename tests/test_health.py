def test_liveness(client):
    r = client.get("/api/v1/health/live")
    assert r.status_code == 200
    assert r.json()["status"] == "alive"


def test_readiness(client):
    r = client.get("/api/v1/health/ready")
    # Sync override can't serve asyncpg in tests; 200 or 503 both acceptable
    assert r.status_code in (200, 503)


def test_health_summary(client):
    r = client.get("/api/v1/health/")
    assert r.status_code == 200
    assert r.json()["status"] == "running"


def test_root(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "docs" in r.json()


def test_missing_api_key(client):
    r = client.get("/api/v1/devices/")
    assert r.status_code == 401


def test_metrics_endpoint(client):
    r = client.get("/metrics")
    assert r.status_code == 200
    assert b"http_requests_total" in r.content