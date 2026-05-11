HEADERS = {"X-API-Key": "sw-admin-changeme-in-prod"}


def test_create_device(client):
    r = client.post(
        "/api/v1/devices/",
        json={"name": "test-marine-0001", "vertical": "marine",
              "location": "Test Port", "status": "online"},
        headers=HEADERS,
    )
    assert r.status_code in (201, 409)


def test_list_devices(client):
    r = client.get("/api/v1/devices/?limit=10", headers=HEADERS)
    assert r.status_code == 200
    assert len(r.json()) > 0


def test_fleet_stats(client):
    r = client.get("/api/v1/devices/stats", headers=HEADERS)
    assert r.status_code == 200
    data = r.json()
    assert data["total_devices"] >= 500
    assert "by_vertical" in data


def test_get_device_by_id(client, sample_device):
    r = client.get(f"/api/v1/devices/{sample_device['id']}", headers=HEADERS)
    assert r.status_code == 200
    assert r.json()["id"] == sample_device["id"]


def test_get_device_not_found(client):
    r = client.get("/api/v1/devices/nonexistent-000", headers=HEADERS)
    assert r.status_code == 404


def test_update_device(client, sample_device):
    r = client.patch(
        f"/api/v1/devices/{sample_device['id']}",
        json={"status": "degraded"},
        headers=HEADERS,
    )
    assert r.status_code == 200
    assert r.json()["status"] == "degraded"


def test_filter_by_vertical(client):
    r = client.get("/api/v1/devices/?vertical=aviation&limit=5", headers=HEADERS)
    assert r.status_code == 200
    for d in r.json():
        assert d["vertical"] == "aviation"


def test_unauthorized_no_key(client):
    r = client.get("/api/v1/devices/")
    assert r.status_code == 401


def test_unauthorized_wrong_key(client):
    r = client.get("/api/v1/devices/", headers={"X-API-Key": "invalid"})
    assert r.status_code == 401