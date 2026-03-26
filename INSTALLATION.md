# EmpathyEngine Installation Guide

## Quick Install

### Prerequisites
- Python 3.8 or higher
- pip package manager
- (Optional) ffmpeg for audio processing

### Basic Installation

```bash
# Clone or navigate to the project
cd /path/to/EmpathyEngine

# Install dependencies
pip install -r requirements.txt

# Install as editable package (recommended for development)
pip install -e .
```

### With API Support

```bash
# Install with API extras
pip install -e ".[api]"
```

### With Development Tools

```bash
# Install with dev tools (pytest, black, flake8)
pip install -e ".[dev]"
```

## System Dependencies

### Linux (Ubuntu/Debian)

```bash
# Audio processing
sudo apt update
sudo apt install -y ffmpeg portaudio19-dev python3-dev

# For voice analysis
sudo apt install -y libsndfile1
```

### macOS

```bash
# Using Homebrew
brew install ffmpeg portaudio
```

### Windows

```bash
# Download and install ffmpeg from:
# https://ffmpeg.org/download.html

# Add ffmpeg to PATH
```

## Verify Installation

### Test Python Package

```bash
python -c "from empathy_engine import EmpathyEngine; print('✅ EmpathyEngine installed!')"
```

### Test Core Functionality

```bash
python quick_start.py
```

### Test API Server

```bash
# Start server
uvicorn empathy_engine.api.server:app

# In another terminal, test
curl http://localhost:8000/health
```

## Model Downloads

On first use, the following models will be automatically downloaded:

1. **Emotion Detection Model** (~100MB)
   - `j-hartmann/emotion-english-distilroberta-base`
   - Downloads on first call to `analyze_text()` or `analyze_emotions()`

2. **No additional downloads needed** for:
   - VADER (included in vaderSentiment package)
   - YAKE (included in yake package)
   - Librosa (no models required)

3. **Optional NLP model** for entity extraction:
   - `python -m spacy download en_core_web_sm`

## Virtual Environment (Recommended)

### Create Virtual Environment

```bash
# Create venv
python -m venv empathy_venv

# Activate (Linux/Mac)
source empathy_venv/bin/activate

# Activate (Windows)
empathy_venv\Scripts\activate

# Install EmpathyEngine
pip install -r requirements.txt
pip install -e .
```

### Deactivate

```bash
deactivate
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'empathy_engine'"

Solution:
```bash
# Make sure you've installed the package
pip install -e .

# Or add to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/path/to/EmpathyEngine"
```

### "librosa failed to load audio"

Solution:
```bash
# Install ffmpeg
sudo apt install ffmpeg  # Linux
brew install ffmpeg      # macOS

# Verify
ffmpeg -version
```

### "Transformer model download fails"

Solution:
```bash
# Clear cache and retry
rm -rf ~/.cache/huggingface

# Or manually download
python -c "from transformers import pipeline; pipeline('text-classification', model='j-hartmann/emotion-english-distilroberta-base')"
```

### "API server won't start"

Solution:
```bash
# Install API dependencies
pip install -e ".[api]"

# Check port availability
lsof -i :8000

# Use different port
uvicorn empathy_engine.api.server:app --port 8080
```

## Production Deployment

### API Server (Production)

```bash
# Install with production server
pip install gunicorn

# Run with gunicorn
gunicorn empathy_engine.api.server:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

### Environment Variables

```bash
# Optional configuration
export EMPATHY_ENGINE_MODEL_CACHE="/path/to/model/cache"
export EMPATHY_ENGINE_LOG_LEVEL="INFO"
export EMPATHY_ENGINE_ENABLE_SEMANTIC_EMBEDDINGS="true"
export EMPATHY_ENGINE_ENABLE_OPENSMILE="true"
```

## Minimum Requirements

- **Python**: 3.8+
- **RAM**: 2GB minimum, 4GB recommended (for model loading)
- **Disk**: 500MB for dependencies + models
- **CPU**: Any modern CPU (GPU not required)

## Optional GPU Support

For faster transformer inference:

```bash
# Install PyTorch with CUDA support
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Verify GPU
python -c "import torch; print(torch.cuda.is_available())"
```

## Upgrading

```bash
# Pull latest changes
git pull

# Reinstall dependencies
pip install -r requirements.txt --upgrade

# Reinstall package
pip install -e . --upgrade
```

## Uninstall

```bash
# Uninstall package
pip uninstall empathy-engine

# Remove model cache (optional)
rm -rf ~/.cache/huggingface
rm -rf ~/.cache/torch
```

## Next Steps

After installation:

1. Run `python quick_start.py` for interactive demo
2. Try `python examples/basic_usage.py` for full examples
3. Read `README.md` for API documentation
4. Check `CLAUDE.md` for development guide

## Support

For installation issues:
- Check `PROJECT_SUMMARY.md` for architecture overview
- Review examples in `examples/` directory
- Verify all system dependencies are installed
