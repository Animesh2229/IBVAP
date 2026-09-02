"""
IBVAP MQTT store-and-forward (skeleton).
When internet returns, flush local alert queue to HQ broker.
Install: pip install aiomqtt
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List

_queue: List[Dict[str, Any]] = []

BROKER_HOST = os.getenv("IBVAP_MQTT_HOST", "localhost")
BROKER_PORT = int(os.getenv("IBVAP_MQTT_PORT", "1883"))
TOPIC = os.getenv("IBVAP_MQTT_TOPIC", "ibvap/alerts")


def enqueue(alert: Dict[str, Any]) -> None:
    _queue.append(alert)


def pending_count() -> int:
    return len(_queue)


async def flush_to_broker() -> int:
    if not _queue:
        return 0
    try:
        import aiomqtt
    except ImportError:
        return 0
    sent = 0
    try:
        async with aiomqtt.Client(BROKER_HOST, BROKER_PORT) as client:
            while _queue:
                item = _queue[0]
                await client.publish(TOPIC, json.dumps(item))
                _queue.pop(0)
                sent += 1
    except Exception:
        pass
    return sent
