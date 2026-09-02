# IBVAP – Intelligent Border Video Analytics Platform

**Force multiplier for Sashastra Seema Bal (SSB)** — AI intelligence layer on existing CCTV.

> AI assists. Humans decide. Nation secured.

## Demo features (hackathon in-scope)

| Feature | Description |
|--------|-------------|
| **Virtual Fence** | Digital boundary on map; breach raises priority alert |
| **Behavioral Alert Engine** | Dwell / direction / repeated crossing / multi-camera score |
| **Tamper-Evident Local Log** | SHA-256 hash-chain audit (offline-first) |

Also includes: live WebSocket alerts, human-in-the-loop review (verify / discard / escalate), sample Indo-Nepal & Indo-Bhutan BOPs, camera compatibility tiers (RTSP / proprietary / analog→IP).

## Quick start

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

Or from repo root:

```bash
./start.sh
```

Open **http://localhost:8000**

- API docs: http://localhost:8000/docs  
- Health: http://localhost:8000/api/health  
- Simulate alert: UI button or `POST /api/simulator/trigger`

## Architecture (demo)

```
Existing CCTV (simulated cameras)
        → Edge simulator (laptop) — detection + behavioral scoring
        → FastAPI offline-first API — SQLite + SHA-256 hash-chain
        → Dashboard (Leaflet map, live alerts, audit log)
```

## Tech stack

| Layer | Stack |
|-------|--------|
| Edge (demo) | Laptop simulator · Deploy target: Mini-PC N100 / Jetson / Coral |
| Video path | RTSP / ONVIF / Analog→IP |
| AI (production path) | YOLOv8 · ByteTrack · PaddleOCR · watchlist-only face match |
| Backend | FastAPI · SQLite hash-chain · WebSocket · MQTT-ready design |
| Dashboard | Leaflet · Tailwind · human review workflow |

## Privacy

- No default biometric identification of general civilians  
- Watchlist-only face match (production design)  
- Human verification before action  
- Full audit trail on every review decision  

## Project layout

```
backend/
  main.py              # API + edge simulator + hash-chain
  requirements.txt
  static/index.html    # Ops dashboard
docs/
  create_pitch.js      # Pitch deck generator (optional)
start.sh
```

## One-line (judge)

IBVAP adds an intelligence layer to existing CCTV — detecting, prioritising and verifying suspicious activity with privacy safeguards and tamper-evident auditing — so jawans see more, miss less, and act with confidence.
