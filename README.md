# IBVAP – Intelligent Border Video Analytics Platform

**Force multiplier for Sashastra Seema Bal (SSB)**  
Offline-first AI layer on existing CCTV · Privacy-by-design · Tamper-evident audit

> AI assists. Humans decide. Nation secured.

## Features (demo-ready)

| Feature | Status |
|--------|--------|
| Virtual Fence / behavioral alerts | Simulator |
| Multi-country **ANPR (India + Nepal + Bhutan)** | Yes |
| SHA-256 hash-chain audit + human review | Yes |
| Offline dashboard (no CDN – college WiFi safe) | Yes |
| WebSocket live alerts | Yes |
| MQTT store-and-forward | Skeleton |
| Real RTSP / YOLO worker | Skeleton (`camera_worker.py`) |

## Quick start (Windows)

1. Open folder `backend`
2. Double-click **`start.bat`**  
   **or** in CMD:
   ```bat
   cd backend
   python -m pip install fastapi "uvicorn[standard]" pydantic
   python -m uvicorn main:app --host 127.0.0.1 --port 8000
   ```
3. Browser: **http://127.0.0.1:8000**
4. Click **Simulate Detection** / **IN · NP · BT Plate**

## Project layout

```
backend/
  main.py           # FastAPI + routes + WebSocket
  models_db.py      # SQLite models + hash-chain
  sim.py            # Alert simulator (demo edge)
  anpr.py           # IN / NP / BT plate classify
  mqtt_sync.py      # HQ sync skeleton
  camera_worker.py  # Real camera path (stub)
  start.bat         # Windows one-click start
  static/index.html # Offline-friendly dashboard
```

## Real camera later

```
1. VLC me RTSP test
2. pip install opencv-python-headless ultralytics
3. set IBVAP_SIMULATOR=0
4. python camera_worker.py
5. Wire YOLO → same save_alert() as simulator
```

ANPR production: plate crop → PaddleOCR → `anpr.parse_ocr_text()`.

## Note

Dashboard uses **BOP list mode** (no Leaflet CDN) for restricted networks.
