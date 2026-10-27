# EMPATHY Engine - Installation Guide

## Quick Start (3 Steps)

### 1. Download the files
```bash
git clone <your-repo-url>
cd empathy-engine
```

Or download ZIP and extract it.

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

**Note**: First install will download ~500MB of ML models (one-time only).

### 3. Run the demo
```bash
python run_demo.py
```

That's it! You're ready to use EMPATHY.

---

## Detailed Installation

### System Requirements
- Python 3.8 or higher
- 2GB free disk space (for ML models)
- 2GB RAM minimum

### Step-by-Step

#### 1. Check Python version
```bash
python --version
# Should be 3.8 or higher
```

If you don't have Python 3.8+, download from [python.org](https://www.python.org/downloads/)

#### 2. Create virtual environment (recommended)
```bash
# Create virtual environment
python -m venv empathy_venv

# Activate it
# On Linux/Mac:
source empathy_venv/bin/activate
# On Windows:
empathy_venv\Scripts\activate
```

#### 3. Install dependencies
```bash
pip install -r requirements.txt
```

This will install:
- vaderSentiment (sentiment analysis)
- transformers + torch (emotion detection)
- librosa + soundfile (voice analysis)
- yake (keyword extraction)

**First run only**: Transformers will download the emotion model (~100MB).

#### 4. Test installation
```bash
python run_demo.py
```

You should see:
```
============================================================
EMPATHY ENGINE - DEMO
============================================================

Example 1: Happy text
------------------------------------------------------------
Text: 'I'm so excited about this project!'
Emotion detected: joy
Confidence: 85.3%
...
```

---

## Usage Examples

### Basic Text Analysis
```python
from empathy_engine import EmpathyEngine

engine = EmpathyEngine()
result = engine.analyze(text="I'm feeling stressed")

print(f"Emotion: {result['primary_emotion']}")
print(f"Confidence: {result['confidence']:.1%}")
```

### Voice Analysis
```python
# You need a WAV audio file
result = engine.analyze(audio_file="my_recording.wav")

print(f"Voice emotion: {result['primary_emotion']}")
```

### Both (Catch Emotional Masking)
```python
# THE MAGIC - detects when voice contradicts text
result = engine.analyze(
    text="I'm fine",
    audio_file="stressed_voice.wav"
)

if result['fusion']['agreement'] == False:
    print("WARNING: Voice contradicts words!")
```

---

## Converting Audio Files

EMPATHY needs WAV format. Convert other formats:

### From MP3
```bash
ffmpeg -i input.mp3 -ar 22050 -ac 1 output.wav
```

### From M4A (iPhone voice memos)
```bash
ffmpeg -i input.m4a -ar 22050 -ac 1 output.wav
```

### Install ffmpeg
- **Ubuntu/Debian**: `sudo apt install ffmpeg`
- **macOS**: `brew install ffmpeg`
- **Windows**: Download from [ffmpeg.org](https://ffmpeg.org/download.html)

---

## Troubleshooting

### "No module named 'vaderSentiment'"
```bash
# Make sure you installed dependencies
pip install -r requirements.txt
```

### "torch not found" or CUDA errors
```bash
# Install CPU-only version (smaller, no GPU needed)
pip uninstall torch
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

### "librosa can't load audio file"
```bash
# Install ffmpeg (system package, not Python)
sudo apt install ffmpeg
```

### Model download fails
The emotion model downloads automatically on first use. If it fails:

```python
# Manually download
from transformers import pipeline
pipeline("text-classification", model="j-hartmann/emotion-english-distilroberta-base")
```

### "externally-managed-environment" error (Linux)
Use virtual environment:
```bash
python -m venv empathy_venv
source empathy_venv/bin/activate
pip install -r requirements.txt
```

---

## What You Get

After installation, you have:

**Files:**
- `empathy_engine.py` - Main engine
- `text_analysis.py` - Text analyzer
- `voice_analysis.py` - Voice analyzer
- `fusion.py` - Cross-modality fusion
- `run_demo.py` - Working examples
- `FUNCTIONS.md` - Complete function reference
- `requirements.txt` - Dependencies

**Capabilities:**
- Analyze text for 7 emotions
- Analyze voice for 7 prosody emotions
- Detect emotional masking (voice vs text)
- Extract keywords and themes
- Measure authenticity

---

## For GitHub Distribution

### Files to include in repo:
```
empathy-engine/
├── empathy_engine.py
├── text_analysis.py
├── voice_analysis.py
├── fusion.py
├── run_demo.py
├── requirements.txt
├── INSTALL.md (this file)
├── FUNCTIONS.md
├── README.md
└── LICENSE
```

### Create README.md:
Include:
- What EMPATHY does
- Quick start (3 steps above)
- Link to FUNCTIONS.md
- Link to INSTALL.md
- Example usage
- License info

### Add .gitignore:
```
__pycache__/
*.pyc
*.pyo
*.wav
*.mp3
empathy_venv/
.DS_Store
```

---

## Next Steps

1. Read `FUNCTIONS.md` for complete function reference
2. Run `python run_demo.py` to see examples
3. Try analyzing your own text/audio
4. Check out the 7 real-world use cases in FUNCTIONS.md

---

## Support

For issues, questions, or feature requests:
- Check FUNCTIONS.md for detailed documentation
- Review troubleshooting section above
- Open an issue on GitHub

---

**EMPATHY Engine v0.1.0**
Extracted from MoodRing (Nov 2025)
Nurdrope
