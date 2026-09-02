"""
IBVAP Multi-Country ANPR
India (IN) + Nepal (NP) + Bhutan (BT) number-plate detect / normalize / classify.

Production path: YOLO plate crop → PaddleOCR (en + hi) → normalize → classify.
Demo path: synthetic plates + same classifier used on OCR text.
"""
from __future__ import annotations

import re
import random
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class PlateCountry(str, Enum):
    INDIA = "IN"
    NEPAL = "NP"
    BHUTAN = "BT"
    UNKNOWN = "UN"


@dataclass
class PlateResult:
    raw_text: str
    normalized: str
    country: str
    confidence: float
    format_hint: str
    region_hint: str = ""
    watchlist_hit: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


DEVANAGARI_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")


def normalize_plate_text(text: str) -> str:
    if not text:
        return ""
    t = text.strip().upper()
    t = t.translate(DEVANAGARI_DIGITS)
    t = re.sub(r"[^\w\u0900-\u097F]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    t = t.replace(" ", "")
    return t


def _has_devanagari(text: str) -> bool:
    return bool(re.search(r"[\u0900-\u097F]", text))


INDIA_PATTERNS = [
    re.compile(r"^([A-Z]{2})(\d{1,2})([A-Z]{1,3})(\d{1,4})$"),
    re.compile(r"^([A-Z]{2})(\d{2})(\d{4})$"),
]

NEPAL_PATTERNS = [
    re.compile(r"^([A-Z]{1,3})(\d{1,2})([A-Z]{1,3})(\d{1,4})$"),
    re.compile(r"^([A-Z]{2,3})(\d{3,4})$"),
]

BHUTAN_PATTERNS = [
    re.compile(r"^(BP|BT|TH|PK)(\d{1,2})([A-Z]?)(\d{2,4})$"),
    re.compile(r"^([A-Z]{1,3})(\d{2,5})$"),
]

INDIA_STATES = {
    "AN", "AP", "AR", "AS", "BR", "CH", "CG", "DD", "DL", "GA", "GJ", "HR",
    "HP", "JH", "JK", "KA", "KL", "LA", "LD", "MP", "MH", "MN", "ML", "MZ",
    "NL", "OD", "OR", "PB", "PY", "RJ", "SK", "TN", "TS", "TR", "UP", "UK",
    "UA", "WB", "DN",
}

NEPAL_PREFIXES = {
    "BA", "BAG", "NA", "GA", "LU", "KO", "JA", "ME", "DH", "SE", "MA", "KA",
    "PA", "SA", "HA", "RA", "BH", "NP",
}

BHUTAN_PREFIXES = {"BP", "BT", "TH", "PK", "BTM", "BPC"}


def classify_plate(text: str) -> PlateResult:
    raw = text or ""
    norm = normalize_plate_text(raw)
    if len(norm) < 4:
        return PlateResult(raw, norm, PlateCountry.UNKNOWN.value, 0.2, "too_short")

    if _has_devanagari(raw) or _has_devanagari(norm):
        return PlateResult(raw, norm, PlateCountry.NEPAL.value, 0.88, "devanagari_script", "Nepal")

    for pat in INDIA_PATTERNS:
        m = pat.match(norm)
        if m:
            st = m.group(1)
            if st in INDIA_STATES:
                return PlateResult(raw, norm, PlateCountry.INDIA.value, 0.92, "in_rto_format", st)

    for pat in BHUTAN_PATTERNS:
        m = pat.match(norm)
        if m:
            prefix = m.group(1)
            if prefix in BHUTAN_PREFIXES or norm.startswith("BP") or norm.startswith("BT"):
                return PlateResult(raw, norm, PlateCountry.BHUTAN.value, 0.86, "bt_vehicle_format", prefix)

    for pat in NEPAL_PATTERNS:
        m = pat.match(norm)
        if m:
            prefix = m.group(1)
            if prefix in NEPAL_PREFIXES or (prefix not in INDIA_STATES and 5 <= len(norm) <= 11):
                conf = 0.78 if prefix in NEPAL_PREFIXES else 0.62
                return PlateResult(raw, norm, PlateCountry.NEPAL.value, conf, "np_latin_format", prefix)

    if norm.startswith("BP") or norm.startswith("BT"):
        return PlateResult(raw, norm, PlateCountry.BHUTAN.value, 0.7, "bt_prefix", norm[:2])
    if any(norm.startswith(p) for p in ("BA", "NA", "GA", "LU", "KO")):
        return PlateResult(raw, norm, PlateCountry.NEPAL.value, 0.65, "np_prefix_heuristic", norm[:2])
    if len(norm) >= 6 and norm[:2] in INDIA_STATES:
        return PlateResult(raw, norm, PlateCountry.INDIA.value, 0.7, "in_state_heuristic", norm[:2])

    return PlateResult(raw, norm, PlateCountry.UNKNOWN.value, 0.35, "unmatched")


_INDIA_SAMPLES = [
    "WB24AB1290", "BR01CD4412", "AS10EF7781", "SK02GH3344", "UP16JK5521",
    "DL3CAB1234", "MH12DE1433", "HR26DK8337", "UK07AB9912", "NL01A2234",
]
_NEPAL_SAMPLES = [
    "BA1PA1234", "NA2KHA567", "GA3CHA891", "LU4JA2345", "KO1PA7788",
    "BAG12PA345", "ME2NA9012", "DH1KA4455",
]
_BHUTAN_SAMPLES = [
    "BP1A1234", "BP2B5678", "BT1C9012", "BP12A345", "TH1A7788", "PK2B3344",
]


def random_demo_plate(country: Optional[str] = None) -> PlateResult:
    c = country or random.choice(["IN", "NP", "BT"])
    if c == "IN":
        raw = random.choice(_INDIA_SAMPLES)
    elif c == "NP":
        raw = random.choice(_NEPAL_SAMPLES)
    else:
        raw = random.choice(_BHUTAN_SAMPLES)
    if random.random() < 0.15:
        raw = raw[:2] + " " + raw[2:]
    result = classify_plate(raw)
    result.confidence = min(0.98, result.confidence + random.uniform(0.0, 0.06))
    return result


def parse_ocr_text(ocr_text: str, watchlist: Optional[List[str]] = None) -> PlateResult:
    result = classify_plate(ocr_text)
    if watchlist:
        wl = {normalize_plate_text(x) for x in watchlist}
        if result.normalized in wl:
            result.watchlist_hit = True
            result.confidence = min(0.99, result.confidence + 0.05)
    return result


DEFAULT_WATCHLIST = [
    "WB24AB1290",
    "BA1PA1234",
    "BP1A1234",
]
