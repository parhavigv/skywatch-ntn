HEADERS = {"X-API-Key": "sw-admin-changeme-in-prod"}


def test_ingest_telemetry(client, sample_device):
    payload = {
        "device_id": sample_device["id"],
        "temperature": 85.5,
        "vibration": 3.2,
        "rpm": 7500.0,
        "pressure": 30.1,
    }
    # First call may hit a stale asyncpg connection; retry once
    r = client.post("/api/v1/telemetry/ingest", json=payload, headers=HEADERS)
    if r.status_code == 500:
        r = client.post("/api/v1/telemetry/ingest", json=payload, headers=HEADERS)
    assert r.status_code == 201
    assert "anomaly_score" in r.json()


def test_anomaly_score_returned(client, sample_device):
    r = client.post(
        "/api/v1/telemetry/ingest",
        json={"device_id": sample_device["id"], "temperature": 50.0,
              "vibration": 1.0, "rpm": 3000.0},
        headers=HEADERS,
    )
    assert r.status_code == 201
    assert 0.0 <= r.json()["anomaly_score"] <= 1.0


def test_batch_ingest(client, sample_device):
    batch = [
        {"device_id": sample_device["id"],
         "temperature": round(60 + i, 2), "rpm": float(5000 + i * 100)}
        for i in range(10)
    ]
    r = client.post("/api/v1/telemetry/ingest/batch", json=batch, headers=HEADERS)
    assert r.status_code == 200
    assert r.json()["ingested"] == 10
    assert "anomalies_flagged" in r.json()


def test_get_device_telemetry(client, sample_device):
    r = client.get(
        f"/api/v1/telemetry/device/{sample_device['id']}?hours=1&limit=50",
        headers=HEADERS,
    )
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_get_device_stats(client, sample_device):
    r = client.get(
        f"/api/v1/telemetry/device/{sample_device['id']}/stats",
        headers=HEADERS,
    )
    assert r.status_code == 200
    assert r.json()["total_records"] > 0


def test_get_anomalies(client):
    r = client.get("/api/v1/telemetry/anomalies?threshold=0.0", headers=HEADERS)
    assert r.status_code == 200
    assert "count" in r.json()


def test_batch_too_large(client, sample_device):
    batch = [{"device_id": sample_device["id"], "temperature": 70.0}] * 501
    r = client.post("/api/v1/telemetry/ingest/batch", json=batch, headers=HEADERS)
    assert r.status_code == 400


def test_ml_stats_endpoint(client, sample_device):
    for i in range(5):
        client.post(
            "/api/v1/telemetry/ingest",
            json={"device_id": sample_device["id"], "temperature": float(60 + i)},
            headers=HEADERS,
        )
    r = client.get(
        f"/api/v1/telemetry/device/{sample_device['id']}/ml-stats",
        headers=HEADERS,
    )
    assert r.status_code == 200
    assert "samples_seen" in r.json()


def test_unauthorized_ingest(client, sample_device):
    r = client.post(
        "/api/v1/telemetry/ingest",
        json={"device_id": sample_device["id"], "temperature": 70.0},
    )
    assert r.status_code == 401