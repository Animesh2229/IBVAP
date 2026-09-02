"""IBVAP WebSocket hub and edge alert simulator."""
from __future__ import annotations

import asyncio
import json
import random
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

from fastapi import WebSocket

from models_db import (
    Alert,
    AlertSeverity,
    AlertType,
    append_audit,
    get_conn,
)
from anpr import random_demo_plate, parse_ocr_text, DEFAULT_WATCHLIST, PlateCountry

class ConnectionManager:
    def __init__(self) -> None:
        self.active: Set[WebSocket] = set()

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self.active.add(ws)

    def disconnect(self, ws: WebSocket) -> None:
        self.active.discard(ws)

    async def broadcast(self, message: Dict[str, Any]) -> None:
        dead: List[WebSocket] = []
        data = json.dumps(message)
        for ws in list(self.active):
            try:
                await ws.send_text(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


manager = ConnectionManager()
simulator_task: Optional[asyncio.Task] = None
simulator_running = False


ALERT_TEMPLATES = [
    {
        "type": AlertType.VIRTUAL_FENCE,
        "severity": AlertSeverity.HIGH,
        "title": "Virtual Fence Breach",
        "description": "Person detected crossing into restricted digital boundary.",
        "score_range": (0.72, 0.95),
    },
    {
        "type": AlertType.LOITERING,
        "severity": AlertSeverity.MEDIUM,
        "title": "Loitering Detected",
        "description": "Prolonged dwell time in sensitive zone (behavioral score elevated).",
        "score_range": (0.55, 0.82),
    },
    {
        "type": AlertType.DIRECTION,
        "severity": AlertSeverity.MEDIUM,
        "title": "Anomalous Movement Direction",
        "description": "Subject moving against expected patrol / traffic pattern.",
        "score_range": (0.50, 0.78),
    },
    {
        "type": AlertType.REPEATED_CROSSING,
        "severity": AlertSeverity.HIGH,
        "title": "Repeated Zone Crossing",
        "description": "Same track crossed critical zone multiple times within window.",
        "score_range": (0.68, 0.92),
    },
    {
        "type": AlertType.ZONE_DWELL,
        "severity": AlertSeverity.CRITICAL,
        "title": "Critical Zone Dwell",
        "description": "Extended presence inside high-risk corridor after dark.",
        "score_range": (0.80, 0.98),
    },
    {
        "type": AlertType.MULTI_CAMERA,
        "severity": AlertSeverity.HIGH,
        "title": "Multi-Camera Correlation",
        "description": "Same subject linked across adjacent cameras – priority elevated.",
        "score_range": (0.75, 0.94),
    },
    {
        "type": AlertType.ANPR,
        "severity": AlertSeverity.HIGH,
        "title": "ANPR – Number Plate Detected",
        "description": "Multi-country plate read (India / Nepal / Bhutan).",
        "score_range": (0.70, 0.96),
    },
]


def list_cameras() -> List[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM cameras")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def save_alert(alert: Alert) -> None:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO alerts (id, type, severity, title, description, camera_id, bop_id, score, timestamp, lat, lng, status, metadata)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            alert.id,
            alert.type.value,
            alert.severity.value,
            alert.title,
            alert.description,
            alert.camera_id,
            alert.bop_id,
            alert.score,
            alert.timestamp,
            alert.lat,
            alert.lng,
            alert.status,
            json.dumps(alert.metadata),
        ),
    )
    conn.commit()
    conn.close()
    append_audit(
        "alert_created",
        {
            "alert_id": alert.id,
            "type": alert.type.value,
            "severity": alert.severity.value,
            "camera_id": alert.camera_id,
            "bop_id": alert.bop_id,
            "score": alert.score,
        },
    )


async def generate_simulated_alert() -> Optional[Alert]:
    cams = [c for c in list_cameras() if c["status"] != "offline"]
    if not cams:
        return None
    cam = random.choice(cams)
    tmpl = random.choice(ALERT_TEMPLATES)
    score = round(random.uniform(*tmpl["score_range"]), 3)
    meta = {
        "dwell_sec": random.randint(30, 420) if tmpl["type"] in (AlertType.LOITERING, AlertType.ZONE_DWELL) else None,
        "direction_deg": random.randint(0, 359) if tmpl["type"] == AlertType.DIRECTION else None,
        "track_id": f"trk-{random.randint(1000, 9999)}",
        "model": "YOLOv8n+ByteTrack (sim)",
        "offline": True,
    }
    title = tmpl["title"]
    description = tmpl["description"]
    severity = tmpl["severity"]

    if tmpl["type"] == AlertType.ANPR:
        plate = random_demo_plate()
        plate = parse_ocr_text(plate.raw_text, DEFAULT_WATCHLIST)
        country_name = {"IN": "India", "NP": "Nepal", "BT": "Bhutan"}.get(plate.country, "Unknown")
        title = f"ANPR – {country_name} Plate"
        description = (
            f"Plate {plate.normalized} classified as {country_name} "
            f"({plate.country}). Format: {plate.format_hint}."
        )
        if plate.watchlist_hit:
            severity = AlertSeverity.CRITICAL
            title = f"ANPR WATCHLIST – {country_name} {plate.normalized}"
            description = (
                f"Watchlist hit: {plate.normalized} ({country_name}). "
                f"Cross-border priority. Region hint: {plate.region_hint or '—'}."
            )
        meta.update({
            "anpr": plate.to_dict(),
            "plate": plate.normalized,
            "plate_country": plate.country,
            "plate_country_name": country_name,
            "model": "ANPR-MultiCountry (IN/NP/BT) + YOLOv8n (sim)",
        })
        score = round(plate.confidence, 3)

    alert = Alert(
        id=str(uuid.uuid4()),
        type=tmpl["type"],
        severity=severity,
        title=title,
        description=description,
        camera_id=cam["id"],
        bop_id=cam["bop_id"],
        score=score,
        timestamp=datetime.now(timezone.utc).isoformat(),
        lat=cam["lat"] + random.uniform(-0.002, 0.002),
        lng=cam["lng"] + random.uniform(-0.002, 0.002),
        metadata=meta,
    )
    save_alert(alert)
    return alert


async def simulator_loop() -> None:
    global simulator_running
    simulator_running = True
    for _ in range(4):
        a = await generate_simulated_alert()
        if a:
            await manager.broadcast({"event": "alert", "data": a.model_dump()})
        await asyncio.sleep(0.4)
    while simulator_running:
        await asyncio.sleep(random.uniform(8, 18))
        if not simulator_running:
            break
        a = await generate_simulated_alert()
        if a:
            await manager.broadcast({"event": "alert", "data": a.model_dump()})
