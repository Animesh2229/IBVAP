#!/bin/bash
cd "$(dirname "$0")/backend"
echo "Starting IBVAP on http://0.0.0.0:8000 ..."
exec python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
