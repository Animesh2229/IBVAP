"""IBVAP FastAPI application entrypoint."""
from __future__ import annotations

import asyncio
import json
import random
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

import sim as sim_mod
from models_db import (
    GENESIS_HASH,
    SAMPLE_BOPS,
    BOP,
    Alert,
    DashboardStats,
    HumanReviewAction,
    append_audit,
    get_conn,
    init_db,
    seed_if_empty,
    verify_chain,
)
from sim import (
    generate_simulated_alert,
    list_cameras,
    manager,
    simulator_loop,
)
from anpr import parse_ocr_text, random_demo_plate, DEFAULT_WATCHLIST, classify_plate

simulator_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global simulator_task
    init_db()
    seed_if_empty()
    simulator_task = asyncio.create_task(simulator_loop())
    yield
    sim_mod.simulator_running = False
    if simulator_task:
        simulator_task.cancel()
        try:
            await simulator_task
        except asyncio.CancelledError:
            pass


app = FastAPI(
    title="IBVAP API",
    description="Intelligent Border Video Analytics Platform – Offline-first edge API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = Path(__file__).parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
def root_page():
    index = STATIC_DIR / "index.html"
    if index.exists():
        return FileResponse(str(index))
    return {"service": "IBVAP", "docs": "/docs"}


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": "IBVAP",
        "mode": "edge-simulator",
        "offline_first": True,
        "chain_valid": verify_chain(),
        "ts": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/bops", response_model=List[BOP])
def get_bops():
    return SAMPLE_BOPS


@app.get("/api/cameras")
def get_cameras():
    return list_cameras()


@app.get("/api/fences")
def get_fences():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM fence_zones WHERE active = 1")
    rows = []
    for r in cur.fetchall():
        rows.append(
            {
                "id": r["id"],
                "name": r["name"],
                "bop_id": r["bop_id"],
                "polygon": json.loads(r["polygon"]),
                "severity": r["severity"],
                "active": bool(r["active"]),
            }
        )
    conn.close()
    return rows


@app.get("/api/alerts")
def get_alerts(limit: int = 50, status: Optional[str] = None):
    conn = get_conn()
    cur = conn.cursor()
    if status:
        cur.execute(
            "SELECT * FROM alerts WHERE status = ? ORDER BY timestamp DESC LIMIT ?",
            (status, limit),
        )
    else:
        cur.execute("SELECT * FROM alerts ORDER BY timestamp DESC LIMIT ?", (limit,))
    rows = []
    for r in cur.fetchall():
        d = dict(r)
        d["metadata"] = json.loads(d["metadata"])
        rows.append(d)
    conn.close()
    return rows


@app.post("/api/alerts/{alert_id}/review")
async def review_alert(alert_id: str, body: HumanReviewAction):
    if body.action not in ("approve", "discard", "escalate"):
        raise HTTPException(400, "Invalid action")
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM alerts WHERE id = ?", (alert_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        raise HTTPException(404, "Alert not found")
    new_status = {"approve": "resolved", "discard": "discarded", "escalate": "reviewing"}[body.action]
    cur.execute("UPDATE alerts SET status = ? WHERE id = ?", (new_status, alert_id))
    conn.commit()
    conn.close()
    entry = append_audit(
        "human_review",
        {
            "alert_id": alert_id,
            "action": body.action,
            "note": body.note,
            "new_status": new_status,
            "operator": "demo-jawan",
        },
    )
    payload = {
        "event": "alert_updated",
        "data": {"id": alert_id, "status": new_status, "action": body.action},
    }
    await manager.broadcast(payload)
    return {"ok": True, "status": new_status, "audit_hash": entry.hash}


@app.get("/api/audit")
def get_audit(limit: int = 40):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, event_type, payload, prev_hash, hash, timestamp FROM audit_log ORDER BY id DESC LIMIT ?",
        (limit,),
    )
    rows = []
    for r in cur.fetchall():
        rows.append(
            {
                "id": r["id"],
                "event_type": r["event_type"],
                "payload": json.loads(r["payload"]),
                "prev_hash": r["prev_hash"],
                "hash": r["hash"],
                "timestamp": r["timestamp"],
            }
        )
    conn.close()
    return {"chain_valid": verify_chain(), "entries": rows}


@app.get("/api/audit/verify")
def audit_verify():
    valid = verify_chain()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS c FROM audit_log")
    count = cur.fetchone()["c"]
    conn.close()
    return {"valid": valid, "entries": count, "algorithm": "SHA-256", "genesis": GENESIS_HASH[:16] + "…"}


@app.get("/api/stats", response_model=DashboardStats)
def get_stats():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS c FROM alerts")
    total = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) AS c FROM alerts WHERE status = 'open'")
    open_a = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) AS c FROM cameras WHERE status = 'online'")
    online = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) AS c FROM cameras")
    total_cam = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) AS c FROM alerts WHERE status = 'discarded'")
    discarded = cur.fetchone()["c"]
    conn.close()
    far = round((discarded / total) * 100, 1) if total else 0.0
    return DashboardStats(
        total_alerts_24h=total,
        open_alerts=open_a,
        cameras_online=online,
        cameras_total=total_cam,
        avg_response_min=round(random.uniform(1.2, 4.5), 1),
        false_alarm_rate=far,
        bops_covered=len(SAMPLE_BOPS),
        audit_chain_valid=verify_chain(),
    )


@app.post("/api/simulator/trigger")
async def trigger_alert():
    a = await generate_simulated_alert()
    if not a:
        raise HTTPException(500, "No cameras available")
    await manager.broadcast({"event": "alert", "data": a.model_dump()})
    return a


@app.post("/api/anpr/parse")
def anpr_parse(body: dict):
    text = (body or {}).get("text", "")
    watchlist = (body or {}).get("watchlist") or DEFAULT_WATCHLIST
    return parse_ocr_text(text, watchlist).to_dict()


@app.get("/api/anpr/demo")
def anpr_demo(country: str = None):
    if country:
        country = country.upper()
        if country not in ("IN", "NP", "BT"):
            raise HTTPException(400, "country must be IN, NP, or BT")
    plate = random_demo_plate(country)
    return parse_ocr_text(plate.raw_text, DEFAULT_WATCHLIST).to_dict()


@app.post("/api/simulator/trigger_anpr")
async def trigger_anpr(country: str = None):
    from models_db import AlertType, AlertSeverity
    import uuid as _uuid

    cams = [c for c in list_cameras() if c["status"] != "offline"]
    if not cams:
        raise HTTPException(500, "No cameras")
    cam = cams[0]
    if country:
        country = country.upper()
        if country not in ("IN", "NP", "BT"):
            raise HTTPException(400, "country must be IN, NP, or BT")
    plate = parse_ocr_text(random_demo_plate(country).raw_text, DEFAULT_WATCHLIST)
    cname = {"IN": "India", "NP": "Nepal", "BT": "Bhutan"}.get(plate.country, "Unknown")
    sev = AlertSeverity.CRITICAL if plate.watchlist_hit else AlertSeverity.HIGH
    title = f"ANPR WATCHLIST – {cname} {plate.normalized}" if plate.watchlist_hit else f"ANPR – {cname} Plate"
    desc = (
        f"Watchlist hit: {plate.normalized} ({cname})."
        if plate.watchlist_hit
        else f"Plate {plate.normalized} classified as {cname} ({plate.country})."
    )
    alert = Alert(
        id=str(_uuid.uuid4()),
        type=AlertType.ANPR,
        severity=sev,
        title=title,
        description=desc,
        camera_id=cam["id"],
        bop_id=cam["bop_id"],
        score=round(plate.confidence, 3),
        timestamp=datetime.now(timezone.utc).isoformat(),
        lat=cam["lat"],
        lng=cam["lng"],
        metadata={
            "anpr": plate.to_dict(),
            "plate": plate.normalized,
            "plate_country": plate.country,
            "plate_country_name": cname,
            "model": "ANPR-MultiCountry (IN/NP/BT) (sim)",
            "offline": True,
        },
    )
    from sim import save_alert
    save_alert(alert)
    await manager.broadcast({"event": "alert", "data": alert.model_dump()})
    return alert


@app.websocket("/ws/alerts")
async def ws_alerts(ws: WebSocket):
    await manager.connect(ws)
    try:
        await ws.send_text(json.dumps({"event": "connected", "message": "IBVAP live feed"}))
        while True:
            try:
                msg = await asyncio.wait_for(ws.receive_text(), timeout=30)
                if msg == "ping":
                    await ws.send_text(json.dumps({"event": "pong"}))
            except asyncio.TimeoutError:
                await ws.send_text(json.dumps({"event": "heartbeat", "ts": time.time()}))
    except WebSocketDisconnect:
        manager.disconnect(ws)
    except Exception:
        manager.disconnect(ws)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
