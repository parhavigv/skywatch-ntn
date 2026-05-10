# SkyWatch NTN — Cloud-Native IoT Fleet Monitor

![CI/CD](https://github.com/parhavigv/skywatch-ntn/actions/workflows/ci-cd.yml/badge.svg)
![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.136-green)
![Kubernetes](https://img.shields.io/badge/Kubernetes-1.35-blue)
![Tests](https://img.shields.io/badge/tests-18%20passed-brightgreen)

A production-grade cloud-native IoT fleet monitoring platform ingesting real-time telemetry from **500+ simulated devices** across three industrial verticals at **500+ messages/second**.

---

## Key Metrics

| Metric | Value |
|---|---|
| Ingestion throughput | 500+ msg/s |
| Active devices | 500 (167 Aviation, 167 Marine, 166 Power Grid) |
| Test coverage | 18/18 passing (100%) |
| Kubernetes replicas | 2 min to 8 max via HPA |
| Anomaly detection | Real-time scoring per telemetry record |

---

## Tech Stack

| Layer | Technology |
|---|---|
| API | FastAPI 0.136 + Pydantic v2 + Swagger/OpenAPI |
| ORM | SQLAlchemy 2.0 + Alembic migrations |
| Database | PostgreSQL 15 |
| Simulator | Python asyncio — 500 devices, 3 verticals |
| Containers | Docker + docker-compose |
| Orchestration | Kubernetes with HPA, liveness/readiness probes, resource limits |
| CI/CD | GitHub Actions: pytest -> Docker build -> GHCR -> EC2 deploy |
| Testing | pytest + httpx (18 tests, 100% pass rate) |

---

## Device Verticals

**Aviation** — vibration (Hz), temperature, RPM, oil pressure, exhaust temp, altitude

**Marine** — fuel flow (L/h), shaft torque (Nm), sea water temp, exhaust temp, speed (knots)

**Power Grid** — voltage (V), current (A), frequency (Hz), load factor, power factor, THD%

---

## Quick Start

`ash
# Clone
git clone https://github.com/parhavigv/skywatch-ntn.git
cd skywatch-ntn

# Start PostgreSQL
docker compose up postgres -d

# Install and migrate
pip install -r requirements.txt
alembic upgrade head

# Start API
uvicorn app.main:app --reload --port 8000
`

Open http://localhost:8000/docs for the full Swagger UI.

`ash
# Run simulator (second terminal)
python app/simulator/device_simulator.py

# Run tests
pytest tests/ -v
# 18 passed in 0.5s
`

---

## API Endpoints

### Health
| Method | Endpoint | Description |
|---|---|---|
| GET | /api/v1/health/live | Kubernetes liveness probe |
| GET | /api/v1/health/ready | Readiness probe with DB check |

### Devices
| Method | Endpoint | Description |
|---|---|---|
| POST | /api/v1/devices/ | Register a new device |
| GET | /api/v1/devices/ | List devices with filters |
| GET | /api/v1/devices/stats | Fleet statistics |
| PATCH | /api/v1/devices/{id} | Update device |

### Telemetry
| Method | Endpoint | Description |
|---|---|---|
| POST | /api/v1/telemetry/ingest | Single record ingest |
| POST | /api/v1/telemetry/ingest/batch | Batch ingest up to 500 records |
| GET | /api/v1/telemetry/device/{id} | Query device telemetry |
| GET | /api/v1/telemetry/anomalies | Fleet anomaly leaderboard |

---

## Kubernetes Deployment

`ash
minikube start --driver=docker --cpus=2 --memory=4096
kubectl apply -f k8s/
kubectl get pods
kubectl get hpa
`

---

## Anomaly Detection

| Condition | Score |
|---|---|
| Temperature > 90C | +0.4 |
| Vibration > 8.0 Hz | +0.3 |
| RPM > 9000 | +0.2 |
| Voltage out of 200-260V range | +0.3 |

Scores capped at 1.0. Query fleet anomalies: GET /api/v1/telemetry/anomalies?threshold=0.5

---

## CI/CD Pipeline

Every push to main triggers:
1. pytest (18 tests)
2. Docker image build
3. Push to GitHub Container Registry
4. SSH deploy to AWS EC2

---

## Author

Parhavi G.V. — B.Tech AI & ML, Dayananda Sagar University

github.com/parhavigv | linkedin.com/in/g-v-parhavi-b51030298
