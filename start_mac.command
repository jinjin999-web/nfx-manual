#!/bin/bash
cd "$(dirname "$0")"
echo "Starting NFX Manual Server..."
echo "Press Ctrl+C to stop the server."
python3 -m http.server 8080 &
sleep 1
open http://localhost:8080
wait
