#!/usr/bin/env python3
"""
EMPATHY ENGINE - Demo
Shows how to use the emotion detection system
"""

from empathy_engine import EmpathyEngine

print("=" * 60)
print("EMPATHY ENGINE - DEMO")
print("=" * 60)
print()

# Create engine
engine = EmpathyEngine()

# Example 1: Analyze happy text
print("Example 1: Happy text")
print("-" * 60)
text = "I'm so excited about this project!"
result = engine.analyze(text=text)
print(f"Text: '{text}'")
print(f"Emotion detected: {result['primary_emotion']}")
print(f"Confidence: {result['confidence']:.1%}")
print()

# Example 2: Analyze stressed text
print("Example 2: Stressed text")
print("-" * 60)
text = "I'm really overwhelmed with everything right now"
result = engine.analyze(text=text)
print(f"Text: '{text}'")
print(f"Emotion detected: {result['primary_emotion']}")
print(f"Confidence: {result['confidence']:.1%}")
if 'text_analysis' in result:
    print(f"Sentiment: {result['text_analysis']['sentiment_label']} ({result['text_analysis']['sentiment_compound']:.2f})")
    print(f"Keywords: {', '.join(result['text_analysis']['keywords'][:5])}")
print()

# Example 3: Voice + Text (if you have an audio file)
print("Example 3: Voice + Text analysis")
print("-" * 60)
print("To test voice analysis, you need a WAV audio file.")
print()
print("Example usage:")
print('  result = engine.analyze(')
print('      text="I\'m fine",')
print('      audio_file="stressed_voice.wav"')
print('  )')
print()
print("If voice contradicts text, it will detect that!")
print()

print("=" * 60)
print("✅ Demo complete!")
print()
print("To use in your code:")
print("  from empathy_engine import EmpathyEngine")
print("  engine = EmpathyEngine()")
print("  result = engine.analyze(text='your text here')")
print("=" * 60)
