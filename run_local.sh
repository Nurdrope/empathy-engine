#!/usr/bin/env bash
# Run the API on this machine only, with no API keys (local mode).
# Reachable at http://127.0.0.1:8000 from this laptop only; other devices
# can't connect. To serve other machines, set EMPATHY_ENGINE_API_KEYS instead.
cd "$(dirname "$(readlink -f "$0")")"
PY=.venv/bin/python
[ -x "$PY" ] || PY=python3
export EMPATHY_ENGINE_ALLOW_UNAUTHENTICATED=1 HOST=127.0.0.1 PORT="${PORT:-8000}"
echo "EmpathyEngine local mode: http://127.0.0.1:$PORT  (docs: /docs, no key needed)"
exec "$PY" -m empathy_engine.api.server
