import asyncio
import httpx
import random
import uuid
from datetime import datetime
from typing import List, Dict

BASE_URL = "http://127.0.0.1:8000/api/v1"
TOTAL_DEVICES = 500
BATCH_SIZE = 50
INTERVAL_SECONDS = 1.0

VERTICALS = {
    "aviation": {
        "locations": ["Mumbai Airport", "Delhi Airport", "Chennai Airport", "Bengaluru Airport", "Hyderabad Airport"],
        "metrics": lambda: {
            "temperature": round(random.uniform(60, 110), 2),
            "vibration": round(random.uniform(0.5, 12.0), 2),
            "rpm": round(random.uniform(5000, 10000), 2),
            "pressure": round(random.uniform(28, 35), 2),
            "extra_metrics": {
                "oil_pressure": round(random.uniform(40, 80), 2),
                "exhaust_temp": round(random.uniform(400, 700), 2),
                "altitude_ft": round(random.uniform(0, 35000), 0),
            }
        }
    },
    "marine": {
        "locations": ["Mumbai Port", "Chennai Port", "Vizag Port", "Kochi Port", "Kolkata Port"],
        "metrics": lambda: {
            "temperature": round(random.uniform(30, 85), 2),
            "pressure": round(random.uniform(1, 15), 2),
            "fuel_flow": round(random.uniform(100, 500), 2),
            "vibration": round(random.uniform(0.2, 6.0), 2),
            "extra_metrics": {
                "shaft_torque_nm": round(random.uniform(1000, 5000), 2),
                "sea_water_temp": round(random.uniform(20, 32), 2),
                "exhaust_temp": round(random.uniform(250, 450), 2),
                "speed_knots": round(random.uniform(0, 25), 2),
            }
        }
    },
    "power_grid": {
        "locations": ["Delhi Grid", "Mumbai Grid", "Bengaluru Grid", "Chennai Grid", "Pune Grid"],
        "metrics": lambda: {
            "voltage": round(random.uniform(210, 250), 2),
            "current": round(random.uniform(10, 100), 2),
            "temperature": round(random.uniform(25, 75), 2),
            "load_factor": round(random.uniform(0.4, 1.0), 4),
            "extra_metrics": {
                "frequency_hz": round(random.uniform(49.5, 50.5), 3),
                "power_factor": round(random.uniform(0.8, 1.0), 3),
                "thd_percent": round(random.uniform(0.5, 5.0), 2),
            }
        }
    }
}

registered_devices: List[Dict] = []

async def register_all_devices(client: httpx.AsyncClient):
    print(f"Registering {TOTAL_DEVICES} devices...")
    vertical_names = list(VERTICALS.keys())
    tasks = []
    for i in range(TOTAL_DEVICES):
        vertical = vertical_names[i % 3]
        location = random.choice(VERTICALS[vertical]["locations"])
        payload = {
            "name": f"device-{vertical[:3].upper()}-{str(i+1).zfill(4)}",
            "vertical": vertical,
            "location": location,
            "status": "online"
        }
        tasks.append(client.post(f"{BASE_URL}/devices/", json=payload))
        if len(tasks) == 20:
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            for r in responses:
                if isinstance(r, httpx.Response) and r.status_code == 201:
                    registered_devices.append(r.json())
                elif isinstance(r, httpx.Response) and r.status_code == 409:
                    pass  # already exists
            tasks = []
            print(f"  Registered {len(registered_devices)} devices so far...")
    if tasks:
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        for r in responses:
            if isinstance(r, httpx.Response) and r.status_code == 201:
                registered_devices.append(r.json())
    print(f"Registration complete: {len(registered_devices)} devices active")

async def fetch_existing_devices(client: httpx.AsyncClient):
    print("Fetching existing devices from API...")
    r = await client.get(f"{BASE_URL}/devices/?limit=500")
    if r.status_code == 200:
        registered_devices.extend(r.json())
        print(f"Loaded {len(registered_devices)} existing devices")

async def simulate_telemetry(client: httpx.AsyncClient):
    if not registered_devices:
        print("No devices to simulate!")
        return
    batch = []
    sampled = random.sample(registered_devices, min(BATCH_SIZE, len(registered_devices)))
    for device in sampled:
        vertical = device["vertical"]
        metrics = VERTICALS[vertical]["metrics"]()
        batch.append({"device_id": device["id"], **metrics})
    r = await client.post(f"{BASE_URL}/telemetry/ingest/batch", json=batch, timeout=10.0)
    if r.status_code == 200:
        data = r.json()
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] Ingested {data['ingested']} records | Fleet: {len(registered_devices)} devices")
    else:
        print(f"Ingest error: {r.status_code} {r.text}")

async def main():
    print("=" * 60)
    print("  SkyWatch NTN ? IoT Fleet Simulator")
    print("  500 devices | 3 verticals | Real-time telemetry")
    print("=" * 60)
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Check API is up
        try:
            r = await client.get(f"{BASE_URL}/health/live")
            assert r.status_code == 200
            print("API is live. Starting simulation...\n")
        except Exception as e:
            print(f"API not reachable: {e}")
            return

        await fetch_existing_devices(client)
        if len(registered_devices) < TOTAL_DEVICES:
            await register_all_devices(client)

        print(f"\nStarting telemetry loop every {INTERVAL_SECONDS}s...")
        cycle = 0
        while True:
            cycle += 1
            await simulate_telemetry(client)
            if cycle % 30 == 0:
                r = await client.get(f"{BASE_URL}/devices/stats")
                if r.status_code == 200:
                    stats = r.json()
                    print(f"\n--- Fleet Stats --- Total: {stats['total_devices']} | By vertical: {stats['by_vertical']}\n")
            await asyncio.sleep(INTERVAL_SECONDS)

if __name__ == "__main__":
    asyncio.run(main())
