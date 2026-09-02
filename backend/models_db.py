"""IBVAP models, DB, hash-chain, and seed data."""
from __future__ import annotations

import hashlib
import json
import random
import sqlite3
import uuid
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel, Field

DB_PATH = Path(__file__).resolve().parent / "data" / "ibvap.db"
GENESIS_HASH = "0" * 64


class AlertSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertType(str, Enum):
    VIRTUAL_FENCE = "virtual_fence"
    LOITERING = "loitering"
    DIRECTION = "direction"
    REPEATED_CROSSING = "repeated_crossing"
    ZONE_DWELL = "zone_dwell"
    MULTI_CAMERA = "multi_camera"
    ANPR = "anpr"
    SYSTEM = "system"


class CameraStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    DEGRADED = "degraded"


class BOP(BaseModel):
    id: str
    name: str
    lat: float
    lng: float
    sector: str
    cameras: int
    status: str = "active"


class Camera(BaseModel):
    id: str
    name: str
    bop_id: str
    tier: int
    status: CameraStatus
    lat: float
    lng: float
    protocol: str


class FenceZone(BaseModel):
    id: str
    name: str
    bop_id: str
    polygon: List[List[float]]
    severity: AlertSeverity = AlertSeverity.HIGH
    active: bool = True


class Alert(BaseModel):
    id: str
    type: AlertType
    severity: AlertSeverity
    title: str
    description: str
    camera_id: str
    bop_id: str
    score: float
    timestamp: str
    lat: float
    lng: float
    status: str = "open"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AuditEntry(BaseModel):
    id: int
    event_type: str
    payload: Dict[str, Any]
    prev_hash: str
    hash: str
    timestamp: str


class HumanReviewAction(BaseModel):
    action: str
    note: str = ""


class DashboardStats(BaseModel):
    total_alerts_24h: int
    open_alerts: int
    cameras_online: int
    cameras_total: int
    avg_response_min: float
    false_alarm_rate: float
    bops_covered: int
    audit_chain_valid: bool


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = get_conn()
    cur = conn.cursor()
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            payload TEXT NOT NULL,
            prev_hash TEXT NOT NULL,
            hash TEXT NOT NULL,
            timestamp TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS alerts (
            id TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            severity TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            camera_id TEXT NOT NULL,
            bop_id TEXT NOT NULL,
            score REAL NOT NULL,
            timestamp TEXT NOT NULL,
            lat REAL NOT NULL,
            lng REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'open',
            metadata TEXT NOT NULL DEFAULT '{}'
        );
        CREATE TABLE IF NOT EXISTS cameras (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            bop_id TEXT NOT NULL,
            tier INTEGER NOT NULL,
            status TEXT NOT NULL,
            lat REAL NOT NULL,
            lng REAL NOT NULL,
            protocol TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS fence_zones (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            bop_id TEXT NOT NULL,
            polygon TEXT NOT NULL,
            severity TEXT NOT NULL,
            active INTEGER NOT NULL DEFAULT 1
        );
        """
    )
    conn.commit()
    conn.close()


def compute_hash(prev_hash: str, event_type: str, payload: str, timestamp: str) -> str:
    raw = f"{prev_hash}|{event_type}|{payload}|{timestamp}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def append_audit(event_type: str, payload: Dict[str, Any]) -> AuditEntry:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT hash FROM audit_log ORDER BY id DESC LIMIT 1")
    row = cur.fetchone()
    prev_hash = row["hash"] if row else GENESIS_HASH
    ts = datetime.now(timezone.utc).isoformat()
    payload_str = json.dumps(payload, sort_keys=True)
    h = compute_hash(prev_hash, event_type, payload_str, ts)
    cur.execute(
        "INSERT INTO audit_log (event_type, payload, prev_hash, hash, timestamp) VALUES (?, ?, ?, ?, ?)",
        (event_type, payload_str, prev_hash, h, ts),
    )
    conn.commit()
    entry_id = cur.lastrowid
    conn.close()
    return AuditEntry(
        id=entry_id or 0,
        event_type=event_type,
        payload=payload,
        prev_hash=prev_hash,
        hash=h,
        timestamp=ts,
    )


def verify_chain() -> bool:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, event_type, payload, prev_hash, hash, timestamp FROM audit_log ORDER BY id ASC")
    rows = cur.fetchall()
    conn.close()
    expected_prev = GENESIS_HASH
    for r in rows:
        if r["prev_hash"] != expected_prev:
            return False
        recomputed = compute_hash(r["prev_hash"], r["event_type"], r["payload"], r["timestamp"])
        if recomputed != r["hash"]:
            return False
        expected_prev = r["hash"]
    return True


SAMPLE_BOPS: List[BOP] = [
    BOP(id="bop-001", name="BOP Kakarbhitta", lat=26.6450, lng=88.1650, sector="Indo-Nepal East", cameras=4),
    BOP(id="bop-002", name="BOP Panitanki", lat=26.7120, lng=88.4010, sector="Indo-Nepal East", cameras=3),
    BOP(id="bop-003", name="BOP Raxaul", lat=26.9790, lng=84.8510, sector="Indo-Nepal Central", cameras=5),
    BOP(id="bop-004", name="BOP Jogbani", lat=26.3980, lng=87.2590, sector="Indo-Nepal East", cameras=3),
    BOP(id="bop-005", name="BOP Jaigaon", lat=26.8470, lng=89.3760, sector="Indo-Bhutan", cameras=4),
    BOP(id="bop-006", name="BOP Banbasa", lat=28.9870, lng=80.0940, sector="Indo-Nepal West", cameras=3),
]


def seed_if_empty() -> None:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS c FROM cameras")
    if cur.fetchone()["c"] > 0:
        conn.close()
        return

    cameras = []
    tiers = [
        (1, "RTSP/ONVIF"),
        (1, "RTSP/ONVIF"),
        (2, "Proprietary"),
        (3, "Analog→IP"),
    ]
    for bop in SAMPLE_BOPS:
        for i in range(bop.cameras):
            tier, proto = tiers[i % len(tiers)]
            cid = f"{bop.id}-cam-{i+1}"
            cameras.append(
                (
                    cid,
                    f"{bop.name} Cam {i+1}",
                    bop.id,
                    tier,
                    "online" if random.random() > 0.08 else "degraded",
                    bop.lat + random.uniform(-0.012, 0.012),
                    bop.lng + random.uniform(-0.012, 0.012),
                    proto,
                )
            )
    cur.executemany(
        "INSERT INTO cameras (id, name, bop_id, tier, status, lat, lng, protocol) VALUES (?,?,?,?,?,?,?,?)",
        cameras,
    )

    fences = [
        (
            "fence-001",
            "Restricted Corridor – Kakarbhitta",
            "bop-001",
            json.dumps([[26.640, 88.160], [26.640, 88.172], [26.650, 88.172], [26.650, 88.160]]),
            "high",
            1,
        ),
        (
            "fence-002",
            "Night Watch Zone – Raxaul",
            "bop-003",
            json.dumps([[26.974, 84.846], [26.974, 84.858], [26.984, 84.858], [26.984, 84.846]]),
            "critical",
            1,
        ),
        (
            "fence-003",
            "Porous Stretch – Jaigaon",
            "bop-005",
            json.dumps([[26.842, 89.370], [26.842, 89.382], [26.852, 89.382], [26.852, 89.370]]),
            "high",
            1,
        ),
    ]
    cur.executemany(
        "INSERT INTO fence_zones (id, name, bop_id, polygon, severity, active) VALUES (?,?,?,?,?,?)",
        fences,
    )
    conn.commit()
    conn.close()

    append_audit(
        "system_init",
        {
            "message": "IBVAP edge node initialized",
            "mode": "offline-first",
            "hash_algo": "SHA-256",
            "bops": len(SAMPLE_BOPS),
        },
    )
