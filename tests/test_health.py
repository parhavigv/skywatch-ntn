def test_liveness(client):
    r = client.get("/api/v1/health/live")
    assert r.status_code == 200
    assert r.json()["status"] == "alive"

def test_readiness(client):
    r = client.get("/api/v1/health/ready")
    assert r.status_code == 200
    assert r.json()["database"] == "connected"

def test_health_summary(client):
    r = client.get("/api/v1/health/")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "running"
    assert data["database"] == "connected"

def test_root(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "docs" in r.json()
