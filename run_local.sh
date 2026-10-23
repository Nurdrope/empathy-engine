#!/usr/bin/env bash
# Run the API on this machine only, with no API keys (local mode).
# Reachable at http://127.0.0.1:8000 from this laptop only; other devices
# can't connect. To serve other machines, set EMPATHY_ENGINE_API_KEYS instead.
cd "$(dirname "$(readlink -f "$0")")"
PY=.venv/bin/python
[ -x "$PY" ] || PY=python3
export EMPATHY_ENGINE_ALLOW_UNAUTHENTICATED=1 HOST=127.0.0.1 PORT="${PORT:-8000}"

# Once the emotion model is downloaded, stop transformers from contacting
# huggingface.co on every model load (update checks). It only needs the
# network for the first download. An HF_HUB_OFFLINE you set yourself wins.
MODEL_DIR="${HF_HUB_CACHE:-${HF_HOME:-$HOME/.cache/huggingface}/hub}/models--j-hartmann--emotion-english-distilroberta-base"
if [ -z "${HF_HUB_OFFLINE+x}" ]; then
    if [ -d "$MODEL_DIR/snapshots" ]; then
        export HF_HUB_OFFLINE=1
    else
        echo "Emotion model not downloaded yet: staying online so the first analysis can fetch it."
    fi
fi
export HF_HUB_DISABLE_TELEMETRY=1

echo "EmpathyEngine local mode: http://127.0.0.1:$PORT  (docs: /docs, no key needed)"
[ "${HF_HUB_OFFLINE:-0}" = 1 ] && echo "Offline model loading: no calls to huggingface.co"
exec "$PY" -m empathy_engine.api.server
