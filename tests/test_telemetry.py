def test_ingest_telemetry(client, sample_device):
    payload = {
        "device_id": sample_device["id"],
        "temperature": 85.5,
        "vibration": 3.2,
        "rpm": 7500.0,
        "pressure": 30.1
    }
    r = client.post("/api/v1/telemetry/ingest", json=payload)
    assert r.status_code == 201
    data = r.json()
    assert data["device_id"] == sample_device["id"]
    assert "anomaly_score" in data

def test_anomaly_score_high(client, sample_device):
    payload = {
        "device_id": sample_device["id"],
        "temperature": 105.0,
        "vibration": 11.0,
        "rpm": 9500.0,
    }
    r = client.post("/api/v1/telemetry/ingest", json=payload)
    assert r.status_code == 201
    assert r.json()["anomaly_score"] >= 0.5

def test_batch_ingest(client, sample_device):
    batch = [
        {"device_id": sample_device["id"], "temperature": round(60 + i, 2), "rpm": float(5000 + i * 100)}
        for i in range(10)
    ]
    r = client.post("/api/v1/telemetry/ingest/batch", json=batch)
    assert r.status_code == 200
    assert r.json()["ingested"] == 10

def test_get_device_telemetry(client, sample_device):
    r = client.get(f"/api/v1/telemetry/device/{sample_device['id']}?hours=1&limit=50")
    assert r.status_code == 200
    assert isinstance(r.json(), list)

def test_get_device_stats(client, sample_device):
    r = client.get(f"/api/v1/telemetry/device/{sample_device['id']}/stats")
    assert r.status_code == 200
    data = r.json()
    assert "total_records" in data
    assert data["total_records"] > 0

def test_get_anomalies(client):
    r = client.get("/api/v1/telemetry/anomalies?threshold=0.5")
    assert r.status_code == 200
    data = r.json()
    assert "count" in data
    assert data["count"] > 0

def test_batch_too_large(client, sample_device):
    batch = [{"device_id": sample_device["id"], "temperature": 70.0}] * 501
    r = client.post("/api/v1/telemetry/ingest/batch", json=batch)
    assert r.status_code == 400
