# EmpathyEngine - Production Docker Image
# Multi-modal emotional intelligence API

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (for librosa/audio processing)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY requirements.txt .
COPY setup.py .
COPY README.md .
COPY LICENSE .
COPY empathy_engine/ ./empathy_engine/

# Install the package with the API extras (FastAPI, uvicorn, multipart)
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir -e ".[api]"

# Run as an unprivileged user, not root
RUN useradd --create-home --uid 10001 empathy
USER empathy

# Listen on all interfaces inside the container; publish the port with
# `-p 127.0.0.1:8000:8000` (or put it behind a reverse proxy) to control exposure.
# API keys are required at runtime: pass -e EMPATHY_ENGINE_API_KEYS=...
ENV HOST=0.0.0.0 PORT=8000

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()"

# Run the API server
CMD ["python", "-m", "empathy_engine.api.server"]
