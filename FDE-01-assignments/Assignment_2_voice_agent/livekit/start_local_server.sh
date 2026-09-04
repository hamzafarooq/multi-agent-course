#!/usr/bin/env bash
set -euo pipefail

echo "Starting local LiveKit server on http://localhost:7880"
echo "Dev credentials: LIVEKIT_API_KEY=devkey LIVEKIT_API_SECRET=secret"
echo "Press Ctrl-C to stop the server."

docker run --rm \
  -p 7880:7880 \
  -p 7881:7881 \
  -p 7882:7882/udp \
  livekit/livekit-server:latest \
  --bind 0.0.0.0 \
  --node-ip 127.0.0.1 \
  --dev
