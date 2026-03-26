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

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install the package
RUN pip install --no-cache-dir -e .

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()"

# Run the API server
CMD ["python", "-m", "empathy_engine.api.server"]
