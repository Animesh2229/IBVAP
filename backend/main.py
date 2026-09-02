"""
IBVAP – Intelligent Border Video Analytics Platform
Offline-first FastAPI backend with SQLite hash-chain audit log,
WebSocket live alerts, virtual fence, and behavioral scoring.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import random
import sqlite3
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

DB_PATH = Path(__file__).resolve().parent / "data" / "ibvap.db"
GENESIS_HASH = "0" * 64

# See repository history / local artifacts for full implementation.
# Full source is in the release; this placeholder ensures path exists.
# COMPLETE_SOURCE_MARKER
