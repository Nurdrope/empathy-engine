# CLAUDE.md

This file provides guidance to Claude Code when working with the EmpathyEngine codebase.

## Project Overview

**EmpathyEngine** is a standalone multi-modal emotional intelligence system that combines text sentiment analysis, voice prosody detection, and cross-modality fusion to understand authentic human emotional states.

**Extracted from**: MoodRing (November 2025)
**Current Version**: 0.1.0
**Project Owner**: Fire Dragon (1976) / Gertz Holdings

### The Breakthrough

EmpathyEngine's core innovation is **cross-modality fusion** - the ability to detect when voice contradicts text. During the legendary MoodRing session (Nov 21, 2025), it caught fear at 95.9% confidence and detected frustration at 93.3% while the user spoke positive words, proving it could see through emotional masking.

**The Secret Sauce**: When text says "I'm fine" but voice prosody shows frustration, the engine boosts confidence in the voice signal and flags potential emotional masking. This is what makes EmpathyEngine special.

## Architecture

### Core Modules

```
empathy_engine/
├── core/
│   ├── engine.py              # Main unified interface
│   ├── text_analyzer.py       # VADER + Transformers emotion detection
│   ├── voice_analyzer.py      # Librosa prosody analysis
│   ├── pattern_detector.py    # Temporal pattern detection
│   └── fusion.py              # Cross-modality fusion (THE MAGIC)
├── api/
│   └── server.py              # FastAPI REST API
├── models/                    # (Reserved for future custom models)
└── utils/                     # (Reserved for utilities)
```

### Data Flow

1. **Input**: Text and/or audio file
2. **Analysis**:
   - TextAnalyzer → sentiment, emotion, keywords
   - VoiceAnalyzer → prosody features, emotion
3. **Fusion**: EmotionFusion combines signals
   - Agreement → confidence boost
   - Disagreement → voice wins (catches masking)
4. **Pattern Detection** (optional): Historical context
5. **Output**: Unified emotional assessment

## Key Technical Details

### Text Analysis (`text_analyzer.py`)
- **VADER**: Fast sentiment analysis (-1 to +1 compound score)
- **Transformers**: `j-hartmann/emotion-english-distilroberta-base` (7 emotions)
- **YAKE**: Keyword extraction (unsupervised)
- **Lazy Loading**: Transformer model loads on first use to keep startup fast

**Emotions**: joy, sadness, anger, fear, surprise, disgust, neutral

### Voice Analysis (`voice_analyzer.py`)
- **Librosa**: Audio feature extraction (pitch, energy, rhythm, spectral centroid)
- **Prosody Features**:
  - Pitch (F0): mean, std, range
  - Energy (RMS): mean, std
  - Speech rate: onsets per second
  - Spectral centroid: tone brightness
  - Zero-crossing rate: noisiness/breathiness
- **Emotion Classification**: Rule-based matching against emotion profiles

**Emotions**: calm, sad, frustrated, elevated, angry, excited, neutral

### Fusion (`fusion.py`)
- **Compatibility Matrix**: Maps text emotions to compatible voice prosody
- **Agreement Detection**: Checks if text and voice signals align
- **Weight Adjustment**:
  - Agreement → boost both signals
  - Disagreement → boost voice (x1.5), discount text (x0.7)
- **Authenticity Score**: Combination of confidence + agreement boost

### Pattern Detection (`pattern_detector.py`)
- **Anxiety spikes**: Fear/anxiety + negative sentiment + anxiety keywords
- **Low-energy periods**: 2+ consecutive days of low sentiment/sad emotion
- **Overthinking**: Long entries + rumination keywords
- **Mood swings**: Rapid sentiment changes (>0.5 in <6 hours)
- **Time patterns**: Morning/afternoon/evening/night mood averages
- **Weekly patterns**: Day-of-week mood patterns

## Development Workflow

### Adding New Features

When adding features to EmpathyEngine:

1. **Preserve lazy loading**: Models should load on first use, not at import
2. **Type hints**: Use type hints for all function parameters and returns
3. **Docstrings**: Include Args, Returns, and example usage
4. **Independence**: Keep modules independent - no circular dependencies
5. **API compatibility**: If changing core interfaces, update API endpoints

### Module Guidelines

**TextAnalyzer**:
- Short text (<20 words) uses quick VADER-based emotion inference
- Long text uses full transformer analysis
- Always include `force_full` parameter for override

**VoiceAnalyzer**:
- Expects WAV format audio files
- Returns features dict + emotion classification
- Tunable emotion profiles in `__init__`

**Fusion**:
- Takes optional text_analysis and/or voice_analysis
- Returns fusion result with authenticity scoring
- Never fails - gracefully handles missing modalities

**PatternDetector**:
- Works with generic entry dicts (not database-specific)
- Entry format: `{timestamp, text, emotion_primary, sentiment_compound, keywords_json}`
- All pattern functions return dicts with `detected`, `recommendation`, and details

### API Development

When modifying the API (`api/server.py`):

1. **File uploads**: Always use tempfile and cleanup in finally block
2. **Error handling**: Catch exceptions and return HTTPException with details
3. **Request models**: Use Pydantic models for validation
4. **Response format**: Always return JSONResponse
5. **Documentation**: Update endpoint docstrings with request/response examples

### Testing

Manual testing workflow:

```bash
# Test text analysis
python -c "from empathy_engine import EmpathyEngine; e = EmpathyEngine(); print(e.analyze_text('I am stressed'))"

# Test voice analysis (need WAV file)
python -c "from empathy_engine import EmpathyEngine; e = EmpathyEngine(); print(e.analyze_voice('test.wav'))"

# Test API
uvicorn empathy_engine.api.server:app --reload
curl -X POST "http://localhost:8000/analyze/text" -H "Content-Type: application/json" -d '{"text":"I am worried"}'
```

### Dependencies

**Core**:
- numpy, scipy: Numerical operations
- vaderSentiment: Fast sentiment
- transformers, torch: Emotion detection
- librosa, soundfile: Audio analysis
- yake: Keyword extraction

**API** (optional):
- fastapi: REST framework
- uvicorn: ASGI server
- pydantic: Validation

All dependencies use **lazy imports** where possible to keep startup fast.

## Common Development Tasks

### Adding a New Emotion to Voice Analysis

Edit `voice_analyzer.py`:
1. Add emotion profile to `self.emotion_profiles` dict
2. Define feature ranges (pitch_mean, pitch_std, energy_mean, speech_rate, spectral_centroid)
3. Update `get_emotion_description()` with human-readable description

### Adding a New Pattern Detector

Edit `pattern_detector.py`:
1. Add detection method (e.g., `detect_new_pattern`)
2. Call from `detect_all_patterns()`
3. Return dict with `detected`, `recommendation`, and pattern-specific data
4. Add recommendation generator method

### Adding a New API Endpoint

Edit `api/server.py`:
1. Create Pydantic request model if needed
2. Add endpoint with `@app.post()` or `@app.get()`
3. Call appropriate engine method
4. Return JSONResponse
5. Add error handling
6. Update API docs in README.md

### Improving Fusion Logic

Edit `fusion.py`:
1. Modify `EMOTION_COMPATIBILITY` matrix for new mappings
2. Adjust weight multipliers in `fuse()` method
3. Update `_generate_fusion_notes()` for better explanations
4. Test with contradictory text/voice samples

## Important Constraints

### Lazy Loading
Multiple modules use lazy loading to avoid startup delays:
- `text_analyzer.py`: Transformer model loaded on first emotion analysis
- `api/server.py`: Engine initialized once at startup

**When modifying**: Preserve lazy loading patterns. Never import heavy models at module level.

### Entry Format
Pattern detector expects standardized entry format:
```python
{
    'timestamp': '2025-11-21 14:30:00',  # ISO format
    'text': 'entry text',
    'emotion_primary': 'joy',
    'sentiment_compound': 0.7,
    'keywords_json': '["happy", "excited"]',
    'prosody_emotion': 'elevated'  # optional
}
```

**When integrating**: Convert your data to this format before calling pattern detector.

### Audio Format
Voice analyzer expects:
- WAV format
- Sample rate: 22050 Hz (auto-converted by librosa if different)
- Mono or stereo (converted to mono internally)

### Thread Safety
- TextAnalyzer: Thread-safe (transformers pipeline is thread-safe)
- VoiceAnalyzer: Thread-safe (librosa is pure computation)
- PatternDetector: Thread-safe (no state beyond entries list)
- Engine: Thread-safe (no shared mutable state)

API uses single engine instance but FastAPI handles concurrency via async.

## Integration Examples

### MoodRing Integration
MoodRing uses EmpathyEngine like this:

```python
from empathy_engine import EmpathyEngine

engine = EmpathyEngine()

# Analyze journal entry
result = engine.analyze(
    text=journal_text,
    audio_path=voice_recording_path
)

# Save to database
db.save_entry(
    text=journal_text,
    emotion_primary=result['primary_emotion'],
    sentiment_compound=result['text_analysis']['sentiment_compound'],
    prosody_emotion=result['voice_emotion'],
    # ... other fields
)

# Detect patterns (weekly)
entries = db.get_last_30_days()
patterns = engine.detect_patterns(entries, days=30)
```

### Standalone Analysis Tool
```python
from empathy_engine import EmpathyEngine

engine = EmpathyEngine()

while True:
    text = input("How are you feeling? ")
    result = engine.analyze_text(text)
    print(f"\nEmotion: {result['emotion_primary']} ({result['emotion_confidence']:.1%})")
    print(f"Sentiment: {result['sentiment_label']} ({result['sentiment_compound']:+.2f})")
```

## Troubleshooting

### "Model not found" errors
- Transformers model downloads on first use (~100MB)
- Check internet connection or pre-download: `transformers-cli download j-hartmann/emotion-english-distilroberta-base`

### Librosa audio errors
- Install ffmpeg: `sudo apt install ffmpeg`
- Check audio file format with: `file audio.wav`
- Ensure WAV format with: `ffmpeg -i input.mp3 output.wav`

### API won't start
- Check port 8000 availability: `lsof -i :8000`
- Install API dependencies: `pip install -e ".[api]"`
- Check uvicorn installed: `uvicorn --version`

### Low confidence scores
- Short text = VADER quick analysis (lower confidence)
- Use `force_full=True` to force transformer analysis
- Voice analysis needs 2+ seconds of clear speech
- Check microphone quality / background noise

## Project Philosophy

1. **Voice doesn't lie**: When text and voice disagree, trust prosody
2. **Lazy loading**: Fast startup, load models on-demand
3. **Modular design**: Use text, voice, or both - your choice
4. **Privacy-first**: All processing local, no cloud required
5. **Expression is always positive**: Any emotion expressed is valuable data

## Related Projects

- **MoodRing**: Emotional wellness journal (parent project)
- **ECHO**: Multi-agent system (potential integration)
- **Telos**: Knowledge management (potential integration)

## Future Enhancements

Potential areas for expansion:
- Real-time streaming analysis (WebSocket API)
- Additional language support (multilingual models)
- Custom emotion model training (fine-tuning)
- Facial expression analysis (computer vision modality)
- Physiological signal fusion (heart rate, skin conductance)
- Group emotion analysis (meeting/conversation analysis)

## Version History

- **0.1.0** (Dec 2025): Initial extraction from MoodRing
  - Core text, voice, fusion, pattern modules
  - REST API layer
  - Python package structure
