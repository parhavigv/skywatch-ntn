"""
SkyWatch NTN - Fleet Simulator
Streams realistic telemetry for 500 devices across aviation, marine, power_grid verticals.
Run: python simulator/run.py
"""
import asyncio
import random
import httpx
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"
API_KEY = "sw-admin-changeme-in-prod"
HEADERS = {"X-API-Key": API_KEY, "Content-Type": "application/json"}
BATCH_SIZE = 50
INTERVAL_SECONDS = 2.0

DEVICE_PROFILES = {
    "aviation":   {"temp": (60, 120), "vib": (0.5, 8.0), "rpm": (5000, 12000), "voltage": (110, 130)},
    "marine":     {"temp": (30, 90),  "vib": (1.0, 6.0), "rpm": (1000, 4000),  "voltage": (220, 240)},
    "power_grid": {"temp": (40, 95),  "vib": (0.1, 3.0), "rpm": (3000, 3600),  "voltage": (380, 420)},
}


def make_telemetry(device_id: str, vertical: str, inject_anomaly: bool = False) -> dict:
    p = DEVICE_PROFILES[vertical]
    multiplier = random.uniform(2.5, 4.0) if inject_anomaly else 1.0
    return {
        "device_id":   device_id,
        "temperature": round(random.uniform(*p["temp"]) * multiplier, 2),
        "vibration":   round(random.uniform(*p["vib"])  * multiplier, 2),
        "rpm":         round(random.uniform(*p["rpm"])  * multiplier, 2),
        "voltage":     round(random.uniform(*p["voltage"]), 2),
        "current":     round(random.uniform(0.5, 15.0), 2),
        "load_factor": round(random.uniform(0.3, 0.95), 3),
        "pressure":    round(random.uniform(25.0, 45.0), 2),
    }


async def fetch_devices(client: httpx.AsyncClient) -> list[dict]:
    r = await client.get(f"{BASE_URL}/devices/?limit=500", headers=HEADERS)
    r.raise_for_status()
    return r.json()


async def send_batch(client: httpx.AsyncClient, batch: list[dict]) -> dict:
    r = await client.post(f"{BASE_URL}/telemetry/ingest/batch", json=batch, headers=HEADERS)
    r.raise_for_status()
    return r.json()


async def run():
    print(f"[{datetime.now().isoformat()}] SkyWatch Simulator starting...")
    async with httpx.AsyncClient(timeout=30.0) as client:
        for attempt in range(10):
            try:
                r = await client.get(f"{BASE_URL}/health/live")
                if r.status_code == 200:
                    print("API is ready.")
                    break
            except Exception:
                pass
            print(f"Waiting for API... attempt {attempt+1}/10")
            await asyncio.sleep(3)

        devices = await fetch_devices(client)
        if not devices:
            print("No devices found. Run seed first.")
            return

        print(f"Simulating {len(devices)} devices, batch={BATCH_SIZE}, interval={INTERVAL_SECONDS}s")
        tick = 0

        while True:
            tick += 1
            anomaly_device = random.choice(devices) if tick % 10 == 0 else None

            batch = []
            for device in devices:
                inject = anomaly_device and device["id"] == anomaly_device["id"]
                batch.append(make_telemetry(device["id"], device["vertical"], inject_anomaly=inject))

            results = []
            for i in range(0, len(batch), BATCH_SIZE):
                sub = batch[i:i+BATCH_SIZE]
                try:
                    result = await send_batch(client, sub)
                    results.append(result)
                except Exception as e:
                    print(f"Batch error: {e}")

            total_ingested = sum(r.get("ingested", 0) for r in results)
            total_anomalies = sum(r.get("anomalies_flagged", 0) for r in results)
            print(
                f"[tick={tick:04d}] {datetime.now().strftime('%H:%M:%S')} "
                f"ingested={total_ingested} anomalies={total_anomalies}"
                + (f" << ANOMALY on {anomaly_device['name']}" if anomaly_device else "")
            )
            await asyncio.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    asyncio.run(run())
