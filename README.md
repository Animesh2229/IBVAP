# IBVAP – Intelligent Border Video Analytics Platform

**Force multiplier for Sashastra Seema Bal (SSB)** — AI intelligence layer on existing CCTV.

> AI assists. Humans decide. Nation secured.

## Demo features

| Feature | Description |
|--------|-------------|
| **Virtual Fence** | Digital boundary breach alerts |
| **Behavioral Alert Engine** | Dwell / direction / repeated crossing / multi-cam |
| **Tamper-Evident Log** | SHA-256 hash-chain audit |
| **Multi-Country ANPR** | **India + Nepal + Bhutan** plate classify + watchlist |

## Quick start

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

Open **http://localhost:8000**

### ANPR (India / Nepal / Bhutan)

| API | Use |
|-----|-----|
| `POST /api/anpr/parse` | `{"text": "KA01AB1234"}` → country IN/NP/BT |
| `GET /api/anpr/demo?country=NP` | Synthetic Nepal plate |
| `POST /api/simulator/trigger_anpr?country=BT` | Force Bhutan plate alert |

Dashboard buttons: **IN Plate / NP Plate / BT Plate**

Watchlist demo hits: `WB24AB1290` (IN), `BA1PA1234` (NP), `BP1A1234` (BT)

Production path: YOLO plate crop → PaddleOCR (en+hi) → same `classify_plate()`.

## Layout

```
backend/
  main.py          # API + routes
  models_db.py     # models, SQLite, hash-chain
  sim.py           # WebSocket + alert simulator
  anpr.py          # Multi-country plate logic
  mqtt_sync.py     # Store-and-forward skeleton
  static/index.html
```

## One-line

IBVAP adds an intelligence layer to existing CCTV — detecting, prioritising and verifying suspicious activity (including cross-border plates from India, Nepal and Bhutan) with privacy safeguards and tamper-evident auditing.
