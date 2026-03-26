# EMPATHY ENGINE - Complete Function Reference

**Version**: 0.1.0 (Simple Edition)
**Last Updated**: December 25, 2025

---

## Table of Contents

1. [What EMPATHY Can Do](#what-empathy-can-do)
2. [Main API - EmpathyEngine Class](#main-api---empathyengine-class)
3. [Text Analysis Functions](#text-analysis-functions)
4. [Voice Analysis Functions](#voice-analysis-functions)
5. [Fusion Functions](#fusion-functions)
6. [Real-World Use Cases](#real-world-use-cases)
7. [Input/Output Reference](#inputoutput-reference)

---

## What EMPATHY Can Do

EMPATHY Engine detects authentic human emotions by analyzing:

### 1. Text Analysis
- ✅ Detect sentiment (positive/negative/neutral)
- ✅ Identify 7 emotions: joy, sadness, anger, fear, surprise, disgust, neutral
- ✅ Extract keywords and themes
- ✅ Measure emotional confidence (0-100%)
- ✅ Detect avoidance patterns ("I'm fine" when not fine)
- ✅ Flag negative short entries that need follow-up

### 2. Voice Analysis
- ✅ Analyze voice prosody (pitch, tone, rhythm, energy)
- ✅ Detect 7 prosody emotions: calm, sad, frustrated, elevated, angry, excited, neutral
- ✅ Measure pitch variance (emotional intensity)
- ✅ Detect speech rate and rhythm patterns
- ✅ Analyze tone brightness/warmth
- ✅ Extract 9 prosodic features from audio

### 3. Cross-Modality Fusion (THE SECRET SAUCE)
- ✅ Combine text + voice for unified assessment
- ✅ Detect when voice contradicts text (emotional masking)
- ✅ Calculate authenticity score (how "real" the emotion is)
- ✅ Boost confidence when signals agree
- ✅ Flag potential emotional hiding ("I'm fine" + frustrated voice)
- ✅ Generate human-readable fusion explanations

---

## Main API - EmpathyEngine Class

### `EmpathyEngine()`
**Initialize the engine**

```python
from empathy_engine import EmpathyEngine

engine = EmpathyEngine()
```

Creates engine with text analyzer, voice analyzer, and fusion module.

---

### `analyze(text=None, audio_file=None)`
**THE MAIN FUNCTION - Analyze text and/or voice**

```python
# Text only
result = engine.analyze(text="I'm feeling stressed")

# Voice only
result = engine.analyze(audio_file="recording.wav")

# Both (THE MAGIC - catches emotional masking)
result = engine.analyze(
    text="I'm fine",
    audio_file="stressed_voice.wav"
)
```

**Input:**
- `text` (str, optional): Text to analyze
- `audio_file` (str, optional): Path to WAV audio file

**Output:** Dict with:
```python
{
    'primary_emotion': 'frustrated',       # Final emotion
    'confidence': 0.87,                    # 0-1 confidence
    'authenticity': 0.75,                  # How "real" it is (0-1)

    # If text was analyzed:
    'text_analysis': {
        'emotion_primary': 'neutral',
        'emotion_confidence': 0.62,
        'sentiment_label': 'neutral',
        'sentiment_compound': 0.05,
        'keywords': ['fine', 'okay']
    },

    # If voice was analyzed:
    'voice_analysis': {
        'prosody_emotion': 'frustrated',
        'prosody_confidence': 0.91,
        'prosody_features': {...}
    },

    # If BOTH analyzed (fusion result):
    'fusion': {
        'fusion_emotion': 'frustrated',
        'fusion_confidence': 0.87,
        'agreement': False,                 # Text vs voice agreement
        'fusion_notes': 'Text/voice mismatch detected...',
        'authenticity_score': 0.75
    }
}
```

**What it catches:**
- "I'm fine" (text) + frustrated voice = detects hidden frustration
- Happy text + sad voice = detects forced positivity
- Neutral text + angry voice = detects suppressed anger

---

### `analyze_text(text, force_full=False)`
**Analyze text only**

```python
result = engine.analyze_text("I'm really worried about this")
```

**Input:**
- `text` (str): Text to analyze
- `force_full` (bool): Force full transformer analysis (slower but better)

**Output:** Dict with:
```python
{
    'emotion_primary': 'fear',
    'emotion_confidence': 0.78,
    'sentiment_label': 'negative',
    'sentiment_compound': -0.52,
    'sentiment_positive': 0.0,
    'sentiment_negative': 0.35,
    'sentiment_neutral': 0.65,
    'keywords': ['worried'],
    'emotions_json': '{"fear": 0.78, "sadness": 0.15, ...}'
}
```

**How it works:**
- Short text (<20 words): Fast VADER-based inference
- Long text (≥20 words): Full transformer emotion detection
- `force_full=True`: Always use transformer (most accurate)

---

### `analyze_voice(audio_file)`
**Analyze voice prosody only**

```python
result = engine.analyze_voice("stressed_call.wav")
```

**Input:**
- `audio_file` (str): Path to WAV audio file

**Output:** Dict with:
```python
{
    'prosody_emotion': 'frustrated',
    'prosody_confidence': 0.89,
    'prosody_scores': {
        'frustrated': 0.89,
        'angry': 0.72,
        'elevated': 0.61,
        'calm': 0.31,
        ...
    },
    'prosody_features': {
        'pitch_mean': 215.3,        # Hz
        'pitch_std': 42.7,          # Variance (emotional intensity)
        'pitch_range': 187.5,       # Max - min
        'energy_mean': 0.23,        # Loudness
        'energy_std': 0.08,
        'speech_rate': 4.2,         # Syllables/second
        'spectral_centroid': 2847,  # Tone brightness (Hz)
        'zero_crossing_rate': 0.12, # Noisiness/breathiness
        'duration': 8.5             # Seconds
    }
}
```

**Prosody Emotions Detected:**
- **calm**: Low pitch, steady rhythm, moderate energy
- **sad**: Low pitch, slow rhythm, low energy
- **frustrated**: Moderate-high pitch, irregular rhythm, tense tone
- **elevated**: High pitch, fast rhythm, high energy
- **angry**: High pitch, high variance, fast choppy rhythm
- **excited**: Very high pitch, very fast, animated
- **neutral**: Moderate everything

---

## Text Analysis Functions

The `TextAnalyzer` class provides these methods:

### `analyze_sentiment(text)`
**Fast sentiment analysis using VADER**

```python
from text_analysis import TextAnalyzer

analyzer = TextAnalyzer()
result = analyzer.analyze_sentiment("This is terrible!")
```

**Output:**
```python
{
    'sentiment_label': 'negative',     # positive/negative/neutral
    'sentiment_compound': -0.68,       # -1 to +1
    'sentiment_positive': 0.0,
    'sentiment_negative': 0.71,
    'sentiment_neutral': 0.29
}
```

---

### `analyze_emotions(text)`
**Deep emotion detection using transformers**

```python
result = analyzer.analyze_emotions("I'm so excited about this!")
```

**Output:**
```python
{
    'emotion_primary': 'joy',
    'emotion_confidence': 0.92,
    'emotions_json': '{"joy": 0.92, "surprise": 0.05, "neutral": 0.02, ...}'
}
```

**7 Emotions Detected:**
- joy
- sadness
- anger
- fear
- surprise
- disgust
- neutral

---

### `extract_keywords(text)`
**Extract key themes using YAKE**

```python
result = analyzer.extract_keywords(
    "I've been feeling really anxious about work deadlines and my health"
)
```

**Output:**
```python
{
    'keywords_json': '["anxious", "work deadlines", "health"]'
}
```

---

### `is_negative_short(text)`
**Check if entry is short + negative (needs follow-up)**

```python
needs_followup = analyzer.is_negative_short("Not good.")
# Returns: True (short + negative)
```

---

### `is_expressing_emotion(text)`
**Check if user is expressing strong emotion**

```python
expressing = analyzer.is_expressing_emotion("I'm so happy!")
# Returns: True (strong positive emotion)
```

Any strong emotion (positive OR negative) = good engagement.

---

### `is_avoidance(text)`
**Detect avoidance patterns ("I'm fine" when not fine)**

```python
avoiding = analyzer.is_avoidance("fine")
# Returns: True

avoiding = analyzer.is_avoidance("whatever")
# Returns: True
```

**Avoidance words detected:**
- fine, ok, okay, whatever
- nothing, nevermind, idk
- same, normal, alright
- meh, eh, sure, i guess

---

### `get_mood_summary(analysis)`
**Human-readable summary from analysis results**

```python
analysis = analyzer.analyze("I'm feeling really stressed today")
summary = analyzer.get_mood_summary(analysis)
# Returns: "strongly negative | feeling fear | themes: stressed, today"
```

---

## Voice Analysis Functions

The `VoiceAnalyzer` class provides:

### `extract_features(audio_path)`
**Extract 9 prosodic features from audio**

```python
from voice_analysis import VoiceAnalyzer

analyzer = VoiceAnalyzer()
features = analyzer.extract_features("recording.wav")
```

**Output:**
```python
{
    'pitch_mean': 180.5,           # Average fundamental frequency (Hz)
    'pitch_std': 35.2,             # Pitch variance (emotional intensity)
    'pitch_range': 142.8,          # Pitch range (max - min)
    'energy_mean': 0.18,           # Average energy/loudness
    'energy_std': 0.06,            # Energy variance
    'speech_rate': 4.5,            # Syllables per second
    'spectral_centroid': 2340.7,   # Brightness of tone (Hz)
    'zero_crossing_rate': 0.09,    # Noisiness/breathiness
    'duration': 7.2                # Audio duration (seconds)
}
```

---

### `classify_emotion(features)`
**Classify emotion from prosodic features**

```python
features = analyzer.extract_features("audio.wav")
result = analyzer.classify_emotion(features)
```

**Output:**
```python
{
    'emotion': 'frustrated',
    'confidence': 0.87,
    'scores': {
        'frustrated': 0.87,
        'angry': 0.71,
        'elevated': 0.58,
        'calm': 0.32,
        ...
    },
    'features': {...}  # Original features dict
}
```

---

### `get_emotion_description(emotion)`
**Human-readable emotion description**

```python
desc = analyzer.get_emotion_description('frustrated')
# Returns: "Tense or frustrated"

desc = analyzer.get_emotion_description('calm')
# Returns: "Calm and composed"
```

---

## Fusion Functions

The `EmotionFusion` class provides:

### `fuse(text_analysis=None, voice_analysis=None, historical_context=None)`
**THE SECRET SAUCE - Fuse multi-modal signals**

```python
from fusion import EmotionFusion

fusion = EmotionFusion()

# Get text and voice results first
text_result = text_analyzer.analyze("I'm fine")
voice_result = voice_analyzer.analyze("stressed_voice.wav")

# Fuse them
result = fusion.fuse(
    text_analysis=text_result,
    voice_analysis=voice_result
)
```

**Output:**
```python
{
    'primary_emotion': 'frustrated',
    'confidence': 0.91,
    'modalities': ['text', 'voice'],
    'agreement': False,                # Do text and voice agree?
    'authenticity_score': 0.72,        # How "real" is it (0-1)
    'fusion_notes': 'Text/voice mismatch detected: "neutral" (text) vs "frustrated" (voice). Voice tone suggests true emotion: frustrated (91.2% confidence). Possible emotional masking.',
    'text_emotion': 'neutral',
    'voice_emotion': 'frustrated',
    'signals': [...]                   # Debug info
}
```

**How fusion works:**

1. **Agreement** (text and voice match):
   - Boosts confidence of both signals (+20%)
   - High authenticity score
   - Example: Happy text + excited voice = highly confident joy

2. **Disagreement** (text and voice contradict):
   - **Voice wins** (x1.5 weight boost)
   - Text discounted (x0.7 weight)
   - Flags potential emotional masking
   - Example: "I'm fine" + frustrated voice = detects hidden frustration

**This is the breakthrough** - catching when someone says one thing but feels another.

---

### `enhance_with_context(fusion_result, historical_patterns=None)`
**Enhance fusion with historical patterns**

```python
# If you have historical data (future feature)
enhanced = fusion.enhance_with_context(
    fusion_result=result,
    historical_patterns=patterns
)
```

Adds contextual insights from:
- Anxiety spike patterns
- Low-energy periods
- Mood volatility

---

## Real-World Use Cases

### 1. Mental Health Apps
```python
# Detect when someone is masking depression
result = engine.analyze(
    text="Everything's great! 😊",
    audio_file="journal_voice.wav"
)

if result['fusion']['agreement'] == False:
    if result['voice_emotion'] in ['sad', 'frustrated']:
        # Alert: possible emotional masking
        print("⚠️  Voice tone doesn't match positive words")
```

### 2. Customer Service
```python
# Detect frustrated customers even if they're polite
result = engine.analyze(
    text="I understand, thanks for your help",
    audio_file="call_recording.wav"
)

if result['voice_emotion'] == 'frustrated':
    # Escalate to supervisor
    priority = "HIGH"
```

### 3. Therapy/Counseling
```python
# Track emotional authenticity over sessions
result = engine.analyze(
    text=session_transcript,
    audio_file=session_recording
)

authenticity = result['authenticity']
if authenticity < 0.5:
    # Client may be guarded/avoiding
    therapist_note = "Explore emotional authenticity"
```

### 4. HR/Employee Wellness
```python
# Detect burnout in check-ins
result = engine.analyze(text=weekly_checkin)

if result['primary_emotion'] in ['sadness', 'fear']:
    if 'overwhelmed' in result['text_analysis']['keywords']:
        # Flag for wellness intervention
```

### 5. Dating Apps
```python
# Verify authentic interest
result = engine.analyze(
    text="I'd love to meet up!",
    audio_file="voice_message.wav"
)

if result['fusion']['agreement'] == True:
    # Authentic enthusiasm
    match_score += 20
```

### 6. Education
```python
# Detect student stress
result = engine.analyze(text=student_feedback)

if result['primary_emotion'] == 'fear':
    if 'exam' in result['text_analysis']['keywords']:
        # Provide exam anxiety resources
```

### 7. Sales/Negotiation
```python
# Read buyer hesitation
result = engine.analyze(
    text="This looks good",
    audio_file="client_response.wav"
)

if result['voice_emotion'] in ['frustrated', 'neutral']:
    # They're not convinced - address concerns
```

---

## Input/Output Reference

### Text Input Requirements
- **Format**: Plain text string
- **Length**: Any length (optimized for 5-500 words)
- **Language**: English (current version)
- **Encoding**: UTF-8

### Audio Input Requirements
- **Format**: WAV (recommended), MP3 (convert first)
- **Sample Rate**: Any (auto-converted to 22050 Hz)
- **Channels**: Mono or stereo (converted to mono)
- **Duration**: 2+ seconds recommended for accurate prosody
- **Quality**: Clear speech (background noise reduces accuracy)

### Converting Audio Files
```bash
# Convert MP3 to WAV
ffmpeg -i input.mp3 -ar 22050 -ac 1 output.wav

# Convert M4A to WAV
ffmpeg -i input.m4a -ar 22050 -ac 1 output.wav
```

### Output Structure

All functions return Python dicts. Common fields:

**Text Analysis:**
```python
{
    'emotion_primary': str,           # Primary emotion label
    'emotion_confidence': float,      # 0-1 confidence
    'sentiment_label': str,           # positive/negative/neutral
    'sentiment_compound': float,      # -1 to +1
    'keywords': list[str]             # Top 5 keywords
}
```

**Voice Analysis:**
```python
{
    'prosody_emotion': str,           # Primary prosody emotion
    'prosody_confidence': float,      # 0-1 confidence
    'prosody_features': dict,         # 9 prosodic features
    'prosody_scores': dict            # All emotion scores
}
```

**Fusion (Text + Voice):**
```python
{
    'primary_emotion': str,           # Final fused emotion
    'confidence': float,              # 0-1 final confidence
    'authenticity': float,            # 0-1 authenticity score
    'agreement': bool,                # Do modalities agree?
    'fusion_notes': str,              # Human-readable explanation
    'text_analysis': dict,            # Full text results
    'voice_analysis': dict            # Full voice results
}
```

---

## Performance Characteristics

### Speed
- **Text analysis (short)**: ~50ms (VADER quick mode)
- **Text analysis (full)**: ~200-500ms (transformer model)
- **Voice analysis**: ~1-3 seconds (depending on audio length)
- **Fusion**: <10ms (just math)

### Accuracy
- **Text sentiment**: ~85% (VADER benchmark)
- **Text emotion**: ~92% (DistilRoBERTa benchmark)
- **Voice prosody**: ~70-80% (rule-based, tuned on real data)
- **Fusion**: ~90%+ when catching contradictions (MoodRing validation)

### Memory Usage
- **Idle**: ~50 MB
- **With transformer loaded**: ~500 MB
- **Processing audio**: +100-200 MB (temporary)

---

## API Summary

### All Public Methods

**EmpathyEngine:**
- `analyze(text=None, audio_file=None)` - Main unified analysis
- `analyze_text(text, force_full=False)` - Text only
- `analyze_voice(audio_file)` - Voice only

**TextAnalyzer:**
- `analyze(text, force_full=False)` - Full text analysis
- `analyze_quick(text)` - Fast sentiment + inferred emotion
- `analyze_sentiment(text)` - VADER sentiment only
- `analyze_emotions(text)` - Transformer emotion detection
- `extract_keywords(text)` - YAKE keyword extraction
- `is_negative_short(text)` - Check if short + negative
- `is_expressing_emotion(text)` - Check emotional expression
- `is_avoidance(text)` - Detect avoidance patterns
- `get_mood_summary(analysis)` - Human-readable summary

**VoiceAnalyzer:**
- `analyze(audio_path)` - Full voice analysis
- `extract_features(audio_path)` - Extract 9 prosodic features
- `classify_emotion(features)` - Classify from features
- `get_emotion_description(emotion)` - Human-readable description

**EmotionFusion:**
- `fuse(text_analysis, voice_analysis, historical_context)` - Cross-modality fusion
- `enhance_with_context(fusion_result, historical_patterns)` - Add historical context

---

## Dependencies Required

```bash
pip install vaderSentiment transformers torch librosa soundfile yake
```

**Breakdown:**
- `vaderSentiment` - Fast sentiment analysis
- `transformers` - Emotion detection model
- `torch` - PyTorch (transformer dependency)
- `librosa` - Audio feature extraction
- `soundfile` - Audio file loading
- `yake` - Keyword extraction

**Optional:**
- `ffmpeg` - Audio format conversion (system package)

---

## Quick Start Examples

### Example 1: Analyze Text
```python
from empathy_engine import EmpathyEngine

engine = EmpathyEngine()
result = engine.analyze(text="I'm feeling really anxious about tomorrow")

print(f"Emotion: {result['primary_emotion']}")
print(f"Confidence: {result['confidence']:.1%}")
```

### Example 2: Analyze Voice
```python
result = engine.analyze(audio_file="stressed_call.wav")

print(f"Voice emotion: {result['primary_emotion']}")
print(f"Pitch: {result['voice_analysis']['prosody_features']['pitch_mean']:.1f} Hz")
```

### Example 3: Catch Emotional Masking
```python
# Someone says they're fine but sounds stressed
result = engine.analyze(
    text="I'm doing fine, everything's okay",
    audio_file="stressed_voice.wav"
)

if result['fusion']['agreement'] == False:
    print("⚠️  WARNING: Voice contradicts words!")
    print(f"Text says: {result['text_analysis']['emotion_primary']}")
    print(f"Voice shows: {result['voice_analysis']['prosody_emotion']}")
    print(f"True emotion: {result['primary_emotion']} ({result['confidence']:.1%})")
```

---

## License & Attribution

**EMPATHY Engine**
Extracted from MoodRing (November 2025)
Fire Dragon (1976) / Gertz Holdings

This is the standalone emotional intelligence system that powered MoodRing's breakthrough moment on November 21, 2025, when it detected fear at 95.9% confidence and caught frustration beneath positive words at 93.3% accuracy.

---

**End of Function Reference**
