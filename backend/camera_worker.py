"""
IBVAP Camera Worker (skeleton for real CCTV / webcam).

Demo mode uses sim.py. When real cameras are available:
  1. Set IBVAP_SIMULATOR=0
  2. Configure RTSP URLs
  3. Run: python camera_worker.py

Pipeline:
  RTSP/Webcam frame → YOLO detect → track → zone/behavior → ANPR optional
  → save_alert() + WebSocket broadcast (same as simulator).
"""
from __future__ import annotations

import os
import time
from typing import Optional


def _try_import_cv2():
    try:
        import cv2
        return cv2
    except ImportError:
        return None


def open_capture(source: str):
    cv2 = _try_import_cv2()
    if cv2 is None:
        raise RuntimeError("pip install opencv-python-headless")
    if source.isdigit():
        cap = cv2.VideoCapture(int(source))
    else:
        cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open camera source: {source}")
    return cap


def process_loop(source: str = "0", camera_id: str = "cam-local", bop_id: str = "bop-001"):
    cv2 = _try_import_cv2()
    if cv2 is None:
        print("OpenCV not installed. Stub only.")
        print("Install: pip install opencv-python-headless ultralytics")
        return

    cap = open_capture(source)
    frame_i = 0
    print(f"[camera_worker] opened {source} as {camera_id} @ {bop_id}")
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                print("[camera_worker] frame grab failed, retry…")
                time.sleep(1)
                continue
            frame_i += 1
            if frame_i % 30 == 0:
                h, w = frame.shape[:2]
                print(f"[camera_worker] frames={frame_i} size={w}x{h}")
            time.sleep(0.01)
    except KeyboardInterrupt:
        print("[camera_worker] stopped")
    finally:
        cap.release()


if __name__ == "__main__":
    src = os.getenv("IBVAP_CAMERA", "0")
    process_loop(source=src)
