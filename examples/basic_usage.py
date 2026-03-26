"""
EmpathyEngine - Basic Usage Examples
Demonstrates core functionality
"""

from empathy_engine import EmpathyEngine


def text_analysis_example():
    """Example: Basic text analysis."""
    print("=" * 60)
    print("TEXT ANALYSIS EXAMPLE")
    print("=" * 60)

    engine = EmpathyEngine()

    # Simple text analysis
    text = "I'm feeling really stressed and overwhelmed with everything happening"

    result = engine.analyze_text(text)

    print(f"\nInput: '{text}'")
    print(f"\nSentiment: {result['sentiment_label']} ({result['sentiment_compound']:+.2f})")
    print(f"Emotion: {result['emotion_primary']} ({result['emotion_confidence']:.1%} confidence)")

    # Keywords
    import json
    keywords = json.loads(result['keywords_json'])
    print(f"Keywords: {', '.join(keywords)}")

    print("\n" + "=" * 60 + "\n")


def voice_analysis_example(audio_path):
    """Example: Voice prosody analysis."""
    print("=" * 60)
    print("VOICE ANALYSIS EXAMPLE")
    print("=" * 60)

    engine = EmpathyEngine()

    result = engine.analyze_voice(audio_path)

    print(f"\nAudio file: {audio_path}")
    print(f"\nProsody emotion: {result['prosody_emotion']} ({result['prosody_confidence']:.1%} confidence)")

    features = result['prosody_features']
    print(f"\nProsody features:")
    print(f"  Pitch: {features['pitch_mean']:.1f} Hz (±{features['pitch_std']:.1f})")
    print(f"  Energy: {features['energy_mean']:.3f}")
    print(f"  Speech rate: {features['speech_rate']:.1f} syllables/sec")
    print(f"  Duration: {features['duration']:.1f} seconds")

    print("\n" + "=" * 60 + "\n")


def multimodal_fusion_example(audio_path):
    """Example: Multi-modal fusion (THE MAGIC)."""
    print("=" * 60)
    print("MULTI-MODAL FUSION EXAMPLE")
    print("=" * 60)

    engine = EmpathyEngine()

    # Text says positive, but voice might reveal something else
    text = "I'm totally fine, everything's great, no worries at all"

    result = engine.analyze(
        text=text,
        audio_path=audio_path
    )

    print(f"\nText: '{text}'")
    print(f"Audio: {audio_path}")

    print(f"\n{'='*40}")
    print("FUSION RESULT")
    print('='*40)

    print(f"\nPrimary emotion: {result['primary_emotion']} ({result['confidence']:.1%} confidence)")
    print(f"Text emotion: {result['text_emotion']}")
    print(f"Voice emotion: {result['voice_emotion']}")
    print(f"Agreement: {result['agreement']}")
    print(f"Authenticity: {result['authenticity_score']:.1%}")

    print(f"\nFusion notes:")
    print(f"  {result['fusion_notes']}")

    # Get summary
    summary = engine.get_mood_summary(result)
    print(f"\nSummary: {summary}")

    print("\n" + "=" * 60 + "\n")


def pattern_detection_example():
    """Example: Pattern detection from historical data."""
    print("=" * 60)
    print("PATTERN DETECTION EXAMPLE")
    print("=" * 60)

    engine = EmpathyEngine()

    # Simulated historical entries
    from datetime import datetime, timedelta
    import json

    entries = []
    base_date = datetime.now() - timedelta(days=30)

    # Simulate some anxiety entries
    for i in range(5):
        entries.append({
            'timestamp': (base_date + timedelta(days=i*3)).isoformat(),
            'text': 'I am really worried about things',
            'emotion_primary': 'fear',
            'sentiment_compound': -0.6,
            'keywords_json': json.dumps(['worried', 'anxious', 'stress'])
        })

    # Simulate some low-energy entries
    for i in range(3):
        entries.append({
            'timestamp': (base_date + timedelta(days=15+i)).isoformat(),
            'text': 'Feeling tired and unmotivated',
            'emotion_primary': 'sadness',
            'sentiment_compound': -0.4,
            'keywords_json': json.dumps(['tired', 'low energy'])
        })

    # Detect patterns
    patterns = engine.detect_patterns(entries, days=30)

    print(f"\nAnalyzed {len(entries)} entries over 30 days\n")

    # Anxiety spikes
    anxiety = patterns.get('anxiety_spikes', {})
    if anxiety.get('detected'):
        print(f"⚠️  ANXIETY SPIKES DETECTED")
        print(f"   Count: {anxiety['spike_count']}")
        print(f"   Recommendation: {anxiety['recommendation']}")
        print()

    # Low energy
    low_energy = patterns.get('low_energy', {})
    if low_energy.get('detected'):
        print(f"💤 LOW ENERGY PERIODS DETECTED")
        print(f"   Period count: {low_energy['period_count']}")
        for period in low_energy['periods']:
            print(f"   - {period['start']} to {period['end']} ({period['duration']} days)")
        print(f"   Recommendation: {low_energy['recommendation']}")
        print()

    print("=" * 60 + "\n")


def contextual_analysis_example(audio_path):
    """Example: Analysis with historical context."""
    print("=" * 60)
    print("CONTEXTUAL ANALYSIS EXAMPLE")
    print("=" * 60)

    engine = EmpathyEngine()

    # Current entry
    text = "I'm worried about this happening again"

    # Simulated historical entries (same as pattern example)
    from datetime import datetime, timedelta
    import json

    entries = []
    base_date = datetime.now() - timedelta(days=30)

    for i in range(5):
        entries.append({
            'timestamp': (base_date + timedelta(days=i*3)).isoformat(),
            'text': 'I am really worried about things',
            'emotion_primary': 'fear',
            'sentiment_compound': -0.6,
            'keywords_json': json.dumps(['worried', 'anxious', 'stress'])
        })

    # Analyze with context
    result = engine.analyze_with_context(
        text=text,
        audio_path=audio_path,
        entries=entries,
        pattern_days=30
    )

    print(f"\nCurrent entry: '{text}'")
    print(f"\nEmotion: {result['primary_emotion']} ({result['confidence']:.1%})")

    if 'context_notes' in result:
        print(f"\n📊 CONTEXTUAL INSIGHTS:")
        print(f"   {result['context_notes']}")

    patterns = result.get('patterns', {})
    if patterns.get('anxiety_spikes', {}).get('detected'):
        anxiety = patterns['anxiety_spikes']
        print(f"\n⚠️  Pattern detected: {anxiety['spike_count']} anxiety spikes in last 30 days")
        print(f"   {anxiety['recommendation']}")

    print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    print("\n🧠 EMPATHYENGINE EXAMPLES\n")

    # Text analysis (always works)
    text_analysis_example()

    # Voice/multimodal examples (need audio file)
    # Uncomment if you have a WAV file:
    # audio_file = "path/to/your/recording.wav"
    # voice_analysis_example(audio_file)
    # multimodal_fusion_example(audio_file)
    # contextual_analysis_example(audio_file)

    # Pattern detection (always works)
    pattern_detection_example()

    print("✅ Examples complete!\n")
