# EmpathyEngine

[![Tests](https://github.com/Nurdrope/empathy-engine/actions/workflows/tests.yml/badge.svg)](https://github.com/Nurdrope/empathy-engine/actions/workflows/tests.yml)

**Multi-Modal Emotional Intelligence System**

A standalone AI engine that combines text sentiment analysis, voice prosody detection, and cross-modality fusion to understand authentic human emotional states.

## The Origin Story

EmpathyEngine was extracted from **MoodRing** - the emotional wellness journal that went from prototype to validating multi-modal AI in a legendary 9-hour session (Nov 21, 2025). During testing, it caught fear at **95.9% confidence** and detected frustration at **93.3%** while the user spoke positive words - proving it could see through emotional masking and recognize authentic states.

**The Breakthrough:** Voice contradicting text = higher confidence in the real emotion. Someone saying "I'm fine" with frustrated prosody triggers detection of true emotional state. This cross-modality fusion is the "secret sauce" that makes EmpathyEngine special.

## Features

### Multi-Modal Analysis
- **Text Analysis**: VADER sentiment + transformer-based emotion detection
- **Voice Prosody**: Pitch, energy, rhythm analysis for emotional tone
- **Cross-Modality Fusion**: Combines signals for holistic understanding
- **Pattern Detection**: Temporal analysis for cycles, spikes, trends

### The Secret Sauce
EmpathyEngine doesn't just analyze text or voice separately - it **fuses** them:
- Agreeing signals = high confidence, high authenticity
- Contradicting signals = voice wins (catches emotional masking)
- Historical context = pattern-aware emotional assessment

### Both Library & API
- **Python Package**: Import and use directly in your code
- **REST API**: FastAPI-based microservice for remote use

## Installation

### As a Python Package

```bash
# Clone repository
git clone https://github.com/Nurdrope/empathy-engine.git
cd empathy-engine

# Core install: text sentiment (VADER) + voice prosody (librosa)
pip install -e .
```

The core install stays lightweight. Transformer-based emotion detection
(`torch` + `transformers`, ~2GB) is opt-in — without it, the engine still runs
and falls back to fast VADER-based analysis.

### Optional Extras

```bash
pip install -e ".[ml]"    # transformer emotion detection (torch, ~2GB)
pip install -e ".[api]"   # REST API (FastAPI + uvicorn)
pip install -e ".[nlp]"   # embeddings, spaCy entities, readability
pip install -e ".[all]"   # everything
```

### Optional Enhancements

EmpathyEngine ships with hooks for richer NLP, audio features, and config/logging.

```bash
# spaCy language model (entities/linguistics)
python -m spacy download en_core_web_sm
```

Environment toggles:

```bash
export EMPATHY_ENGINE_ENABLE_SEMANTIC_EMBEDDINGS=true
export EMPATHY_ENGINE_ENABLE_OPENSMILE=true
```

When enabled, text analysis can include readability metrics, entity extraction, and
semantic embeddings. Voice analysis can include Praat-based jitter/shimmer and
openSMILE features.

## Quick Start

### Python Library Usage

```python
from empathy_engine import EmpathyEngine

# Initialize engine
engine = EmpathyEngine()

# Analyze text only
result = engine.analyze_text("I'm feeling stressed today")
print(result)
# {
#   'sentiment_label': 'negative',
#   'emotion_primary': 'anxiety',
#   'emotion_confidence': 0.78,
#   ...
# }

# Analyze voice only
result = engine.analyze_voice("recording.wav")
print(result)
# {
#   'prosody_emotion': 'frustrated',
#   'prosody_confidence': 0.93,
#   'prosody_features': {...}
# }

# Multi-modal fusion (THE MAGIC)
result = engine.analyze(
    text="I'm totally fine, everything's great",
    audio_path="recording.wav"
)
print(result)
# {
#   'primary_emotion': 'frustrated',
#   'confidence': 0.89,
#   'agreement': False,  # Text and voice disagree!
#   'authenticity_score': 0.85,
#   'fusion_notes': "Text/voice mismatch detected: 'joy' (text) vs 'frustrated' (voice).
#                    Voice tone suggests true emotion: frustrated (89% confidence).
#                    Possible emotional masking."
# }

# With historical context
result = engine.analyze_with_context(
    text="I'm worried again",
    entries=historical_journal_entries,
    pattern_days=30
)
print(result['patterns'])  # Anxiety spikes, low-energy periods, etc.
```

### API Server Usage

#### Start the server

```bash
# Default (localhost:8000)
python -m empathy_engine.api.server

# Or with uvicorn directly
uvicorn empathy_engine.api.server:app --host 0.0.0.0 --port 8000
```

#### Make API requests

```bash
# Text analysis
curl -X POST "http://localhost:8000/analyze/text" \
  -H "Content-Type: application/json" \
  -d '{"text": "I'm feeling stressed", "force_full": false}'

# Voice analysis
curl -X POST "http://localhost:8000/analyze/voice" \
  -F "file=@recording.wav"

# Multi-modal fusion
curl -X POST "http://localhost:8000/analyze/multimodal" \
  -F "text=I'm fine" \
  -F "file=@recording.wav"

# Pattern detection
curl -X POST "http://localhost:8000/patterns/detect" \
  -H "Content-Type: application/json" \
  -d '{
    "entries": [...],
    "days": 30
  }'

Response envelopes (alpha):

```json
{
  "result": {...},
  "inputs": {...}
}
```

### Example: Full Feature Payloads (Alpha)

High risk (all sensors):

```json
{
  "result": {
    "text_analysis": {
      "text": "I can't go on. I want to die. Nothing helps.",
      "sentiment_label": "negative",
      "sentiment_compound": -0.86,
      "emotion_primary": "sadness",
      "emotion_confidence": 0.92,
      "emotions_json": "{\"sadness\":0.92,\"fear\":0.06,\"anger\":0.02}",
      "keywords_json": "[\"can't go on\",\"want to die\",\"nothing helps\"]",
      "empath_json": "{\"sadness\":0.81,\"neg_emotion\":0.74}",
      "readability_flesch": 64.3,
      "readability_smog": 6.8,
      "readability_ari": 5.9,
      "entities_json": "[]",
      "entities_count": 0,
      "semantic_embedding_json": "[0.012,-0.088,0.044,...]",
      "semantic_embedding_dim": 384,
      "semantic_embedding_model": "all-MiniLM-L6-v2"
    },
    "voice_analysis": {
      "prosody_emotion": "angry",
      "prosody_confidence": 0.81,
      "prosody_scores": {"angry":0.81,"frustrated":0.72,"sad":0.18},
      "prosody_features": {
        "pitch_mean": 246.4,
        "pitch_std": 59.2,
        "pitch_range": 180.1,
        "energy_mean": 0.32,
        "energy_std": 0.08,
        "speech_rate": 6.4,
        "spectral_centroid": 3650.2,
        "zero_crossing_rate": 0.11,
        "duration": 8.7,
        "opensmile_features_json": "{\"F0semitoneFrom27.5Hz_sma3nz_amean\":25.8,...}",
        "opensmile_feature_count": 88,
        "praat_pitch_mean": 241.9,
        "praat_intensity_mean": 76.5,
        "praat_jitter_local": 0.018,
        "praat_shimmer_local": 0.41
      }
    },
    "fusion": {
      "primary_emotion": "distress",
      "confidence": 0.93,
      "agreement": false,
      "authenticity_score": 0.88,
      "fusion_notes": "Text/voice mismatch: sadness vs angry"
    },
    "advanced": {
      "intensity": {"intensity": 0.91, "label": "very_high"},
      "sarcasm": {"sarcasm_detected": false, "confidence": 0.04},
      "crisis": {
        "assessment": {
          "level": "IMMEDIATE",
          "score": 1.0,
          "indicators": [
            "CRITICAL: Suicidal ideation detected - 'want to die'",
            "Severe hopelessness: 'nothing helps'"
          ],
          "patterns": {
            "escalating_distress": {"detected": true, "change": -0.52},
            "prolonged_crisis": {"detected": true, "count": 6},
            "negative_short_count": 3
          },
          "timestamp": "2025-02-14T18:22:11.123456"
        },
        "schema": {
          "risk_assessment": {
            "tier": "critical",
            "confidence": 1.0,
            "signals": {
              "lexical_hits": ["..."],
              "temporal_spike": true,
              "baseline_deviation": 0.0,
              "avoidance_detected": false,
              "negative_short_count": 3
            },
            "notes": "Auto-assessed risk signals (alpha, no user-facing advice)."
          },
          "user_view": {"status": "urgent", "summary": "Risk signals logged."},
          "clinical_view": {"signals": {"level": "IMMEDIATE", "indicators": ["..."]}}
        }
      },
      "baseline": {"mean_sentiment": -0.12, "dominant_emotion": "neutral"},
      "transitions": {"common_transitions": ["neutral -> sadness", "sadness -> fear"]},
      "context": {"context_detected": true, "context_notes": ["recent negative streak"]},
      "congruence": {"congruent": false, "notes": "Voice indicates higher arousal"},
      "prediction": {"next_emotion": "sadness", "confidence": 0.62},
      "triggers": {"top_triggers": ["work", "isolation"]},
      "group": {"group_emotion": "distress", "cohesion": 0.34},
      "cultural": {"adjusted_emotion": "sadness", "confidence": 0.90},
      "coherence": {"coherence_score": 0.48, "notes": "High variance"}
    }
  },
  "inputs": {
    "text": "I can't go on. I want to die. Nothing helps.",
    "audio_path": "recording.wav",
    "entries": [{"text":"...","sentiment_compound":-0.7,"timestamp":"..."}],
    "baseline": {"mean_sentiment": -0.12},
    "group_metadata": {"size": 3},
    "cultural_profile": {"region": "US"}
  }
}
```

Moderate risk (all sensors):

```json
{
  "result": {
    "text_analysis": {
      "text": "I'm anxious about work again and can't sleep.",
      "sentiment_label": "negative",
      "sentiment_compound": -0.41,
      "emotion_primary": "fear",
      "emotion_confidence": 0.74,
      "emotions_json": "{\"fear\":0.74,\"sadness\":0.18,\"anger\":0.08}",
      "keywords_json": "[\"anxious\",\"work\",\"can't sleep\"]",
      "empath_json": "{\"anxiety\":0.62}",
      "readability_flesch": 71.0,
      "readability_smog": 6.4,
      "readability_ari": 5.6,
      "entities_json": "[{\"text\":\"work\",\"label\":\"ORG\"}]",
      "entities_count": 1,
      "semantic_embedding_json": "[0.031,-0.012,0.098,...]",
      "semantic_embedding_dim": 384,
      "semantic_embedding_model": "all-MiniLM-L6-v2"
    },
    "voice_analysis": {
      "prosody_emotion": "frustrated",
      "prosody_confidence": 0.63,
      "prosody_scores": {"frustrated":0.63,"elevated":0.41},
      "prosody_features": {
        "pitch_mean": 210.7,
        "pitch_std": 41.2,
        "pitch_range": 122.9,
        "energy_mean": 0.19,
        "energy_std": 0.05,
        "speech_rate": 4.9,
        "spectral_centroid": 2900.5,
        "zero_crossing_rate": 0.08,
        "duration": 10.3,
        "opensmile_features_json": "{\"F0semitoneFrom27.5Hz_sma3nz_amean\":22.1,...}",
        "opensmile_feature_count": 88,
        "praat_pitch_mean": 205.4,
        "praat_intensity_mean": 68.2,
        "praat_jitter_local": 0.012,
        "praat_shimmer_local": 0.28
      }
    },
    "fusion": {
      "primary_emotion": "anxiety",
      "confidence": 0.77,
      "agreement": true,
      "authenticity_score": 0.79
    },
    "advanced": {
      "intensity": {"intensity": 0.58, "label": "moderate"},
      "sarcasm": {"sarcasm_detected": false, "confidence": 0.12},
      "crisis": {
        "assessment": {"level": "MODERATE", "score": 0.53, "indicators": ["..."]},
        "schema": {"risk_assessment": {"tier": "concern", "confidence": 0.53}}
      },
      "baseline": {"mean_sentiment": -0.05, "dominant_emotion": "neutral"},
      "transitions": {"common_transitions": ["neutral -> fear"]},
      "context": {"context_detected": true, "context_notes": ["sleep disruption"]},
      "congruence": {"congruent": true, "notes": "Text/voice aligned"},
      "prediction": {"next_emotion": "neutral", "confidence": 0.48},
      "triggers": {"top_triggers": ["work"]},
      "group": {"group_emotion": "concern", "cohesion": 0.52},
      "cultural": {"adjusted_emotion": "anxiety", "confidence": 0.74},
      "coherence": {"coherence_score": 0.69}
    }
  },
  "inputs": {
    "text": "I'm anxious about work again and can't sleep.",
    "audio_path": "recording.wav",
    "entries": [{"text":"...","sentiment_compound":-0.3,"timestamp":"..."}]
  }
}
```

Low risk (all sensors):

```json
{
  "result": {
    "text_analysis": {
      "text": "Good day. Took a walk and felt pretty calm.",
      "sentiment_label": "positive",
      "sentiment_compound": 0.51,
      "emotion_primary": "joy",
      "emotion_confidence": 0.66,
      "emotions_json": "{\"joy\":0.66,\"neutral\":0.28,\"surprise\":0.06}",
      "keywords_json": "[\"good day\",\"walk\",\"calm\"]",
      "empath_json": "{\"positive_emotion\":0.71}",
      "readability_flesch": 82.1,
      "readability_smog": 5.2,
      "readability_ari": 4.1,
      "entities_json": "[]",
      "entities_count": 0,
      "semantic_embedding_json": "[0.017,0.065,-0.033,...]",
      "semantic_embedding_dim": 384,
      "semantic_embedding_model": "all-MiniLM-L6-v2"
    },
    "voice_analysis": {
      "prosody_emotion": "calm",
      "prosody_confidence": 0.72,
      "prosody_scores": {"calm":0.72,"neutral":0.58},
      "prosody_features": {
        "pitch_mean": 132.2,
        "pitch_std": 18.4,
        "pitch_range": 61.8,
        "energy_mean": 0.08,
        "energy_std": 0.02,
        "speech_rate": 3.2,
        "spectral_centroid": 1780.3,
        "zero_crossing_rate": 0.05,
        "duration": 7.1,
        "opensmile_features_json": "{\"F0semitoneFrom27.5Hz_sma3nz_amean\":17.4,...}",
        "opensmile_feature_count": 88,
        "praat_pitch_mean": 129.9,
        "praat_intensity_mean": 62.7,
        "praat_jitter_local": 0.006,
        "praat_shimmer_local": 0.12
      }
    },
    "fusion": {
      "primary_emotion": "calm",
      "confidence": 0.82,
      "agreement": true,
      "authenticity_score": 0.84
    },
    "advanced": {
      "intensity": {"intensity": 0.24, "label": "low"},
      "sarcasm": {"sarcasm_detected": false, "confidence": 0.03},
      "crisis": {
        "assessment": {"level": "LOW", "score": 0.0, "indicators": []},
        "schema": {"risk_assessment": {"tier": "monitor", "confidence": 0.0}}
      },
      "baseline": {"mean_sentiment": 0.12, "dominant_emotion": "neutral"},
      "transitions": {"common_transitions": ["neutral -> calm"]},
      "context": {"context_detected": false},
      "congruence": {"congruent": true},
      "prediction": {"next_emotion": "calm", "confidence": 0.57},
      "triggers": {"top_triggers": []},
      "group": {"group_emotion": "positive", "cohesion": 0.71},
      "cultural": {"adjusted_emotion": "calm", "confidence": 0.82},
      "coherence": {"coherence_score": 0.88}
    }
  },
  "inputs": {
    "text": "Good day. Took a walk and felt pretty calm.",
    "audio_path": "recording.wav",
    "entries": [{"text":"...","sentiment_compound":0.3,"timestamp":"..."}]
  }
}
```
```

## Architecture

```
EmpathyEngine
├── TextAnalyzer        # VADER + Transformers (emotion-english-distilroberta-base)
├── VoiceAnalyzer       # Librosa prosody extraction + emotion classification
├── PatternDetector     # Temporal pattern detection (anxiety, energy, swings)
└── EmotionFusion       # Cross-modality fusion (the breakthrough)
```

### Data Flow

1. **Input**: Text and/or voice
2. **Analysis**: Parallel processing of each modality
3. **Fusion**: Cross-modality agreement check
   - Agreement → Boost confidence
   - Disagreement → Voice wins (catches masking)
4. **Context**: Optional pattern enhancement
5. **Output**: Unified emotional assessment

## API Endpoints

- `POST /analyze/text` - Text-only analysis
- `POST /analyze/voice` - Voice-only analysis
- `POST /analyze/multimodal` - Multi-modal fusion
- `POST /analyze/contextual` - Analysis with historical context
- `POST /patterns/detect` - Pattern detection only
- `POST /analyze/batch` - Batch analysis
- `GET /health` - Health check


## Use Cases

### Emotional Wellness Apps
MoodRing uses EmpathyEngine for journal analysis combining written entries with voice recordings.

### Customer Service Analysis
Detect frustrated customers even when they're being polite - voice doesn't lie.

### Mental Health Support
Pattern detection for anxiety cycles, low-energy periods, mood volatility.

### Research & Education
Study emotional authenticity, cross-modality emotion detection, temporal patterns.

### Accessibility Tools
Voice-based emotional analysis for users who can't type easily.

## Models Used

- **VADER**: Fast rule-based sentiment (positive/negative/neutral)
- **j-hartmann/emotion-english-distilroberta-base**: 7-class emotion detection
- **YAKE**: Unsupervised keyword extraction
- **Empath**: Lexicon-based category analysis (themes/context)
- **Librosa**: Audio feature extraction (pitch, energy, rhythm, spectral)
- **spaCy** (optional): Entities/linguistics
- **textstat** (optional): Readability metrics
- **sentence-transformers** (optional): Semantic embeddings
- **Praat/Parselmouth** (optional): Jitter/shimmer + pitch/intensity
- **openSMILE** (optional): Standardized acoustic features

Models are lazy-loaded for performance - first use triggers download/initialization.

## Safety Roadmap (Alpha -> v1.0)

Alpha builds expose full outputs for inspection and logging. For v1.0:

- Split outputs into `user_view` (minimal, non-prescriptive) and `clinical_view`
  (full signals, scores, timelines, and raw inputs).
- Default responses return `user_view` only; `clinical_view` requires an explicit opt-in.
- Add redaction for sensitive strings in logs by default.

Draft schema: [`docs/SAFETY_SCHEMA.md`](docs/SAFETY_SCHEMA.md).

## Technical Details

### Emotion Detection
- **Text**: joy, sadness, anger, fear, surprise, disgust, neutral
- **Voice**: calm, sad, frustrated, elevated, angry, excited, neutral
- **Fusion**: Cross-compatible mapping with authenticity scoring

### Pattern Detection
- Anxiety spikes and cycles
- Low-energy periods (2+ consecutive days)
- Overthinking (entry length + rumination keywords)
- Mood swings (rapid sentiment changes)
- Time-of-day patterns
- Weekly patterns

### Performance
- **Text analysis**: ~100ms (VADER), ~500ms (transformer)
- **Voice analysis**: ~2-5s depending on audio length
- **Lazy loading**: Fast startup, models load on first use

## Development

### Run Tests
```bash
pytest tests/
```

### Code Quality
```bash
black empathy_engine/
flake8 empathy_engine/
```

## Project Philosophy

1. **Privacy-first**: All processing local, no cloud required
2. **Expression is positive**: Any emotion expressed is valuable data
3. **Voice doesn't lie**: Prosody reveals authentic emotional state
4. **Context matters**: Historical patterns enhance understanding
5. **Modular design**: Use what you need (text, voice, or both)

## License

MIT License - See LICENSE file

## Credits

**Created by**: Nurdrope
**Extracted from**: MoodRing Division (Nov 2025)
**The Breakthrough Session**: November 21, 2025 - 9 hours that validated multi-modal emotional AI

## Roadmap

- [x] Core text analysis
- [x] Voice prosody analysis
- [x] Cross-modality fusion
- [x] Pattern detection
- [x] REST API
- [ ] Real-time streaming analysis
- [ ] Additional language support
- [ ] Custom emotion model training
- [ ] WebSocket API
- [ ] Emotion visualization tools

## Contributing

This is the beginning of something bigger. Contributions welcome.

## Links

- **MoodRing**: The emotional wellness app that birthed this engine
- **Documentation**: See `docs/` for detailed guides
- **Examples**: See `examples/` for integration examples
