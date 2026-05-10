def test_create_device(client):
    payload = {"name": "test-marine-0001", "vertical": "marine", "location": "Test Port", "status": "online"}
    r = client.post("/api/v1/devices/", json=payload)
    assert r.status_code in (201, 409)

def test_list_devices(client):
    r = client.get("/api/v1/devices/?limit=10")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
    assert len(r.json()) > 0

def test_fleet_stats(client):
    r = client.get("/api/v1/devices/stats")
    assert r.status_code == 200
    data = r.json()
    assert "total_devices" in data
    assert data["total_devices"] >= 500
    assert "by_vertical" in data

def test_get_device_by_id(client, sample_device):
    r = client.get(f"/api/v1/devices/{sample_device['id']}")
    assert r.status_code == 200
    assert r.json()["id"] == sample_device["id"]

def test_get_device_not_found(client):
    r = client.get("/api/v1/devices/nonexistent-id-000")
    assert r.status_code == 404

def test_update_device(client, sample_device):
    r = client.patch(f"/api/v1/devices/{sample_device['id']}", json={"status": "degraded"})
    assert r.status_code == 200
    assert r.json()["status"] == "degraded"

def test_filter_by_vertical(client):
    r = client.get("/api/v1/devices/?vertical=aviation&limit=10")
    assert r.status_code == 200
    for device in r.json():
        assert device["vertical"] == "aviation"
