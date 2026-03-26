#!/usr/bin/env python3
"""
EmpathyEngine - Quick Start Script
Interactive demo of core functionality
"""

from empathy_engine import EmpathyEngine


def main():
    print("""
╔═══════════════════════════════════════════════════════════════╗
║                                                                 ║
║                      🧠 EMPATHYENGINE                          ║
║                                                                 ║
║         Multi-Modal Emotional Intelligence System               ║
║                                                                 ║
╚═══════════════════════════════════════════════════════════════╝

Welcome to EmpathyEngine - the AI that understands authentic emotions.

The secret? Cross-modality fusion. When your words say "I'm fine" but
your voice says otherwise, we catch it.

Let's test it out!
""")

    engine = EmpathyEngine()

    print("\n" + "="*65)
    print("TEXT ANALYSIS")
    print("="*65 + "\n")

    while True:
        text = input("How are you feeling? (or 'quit' to exit): ").strip()

        if text.lower() in ['quit', 'exit', 'q']:
            break

        if not text:
            continue

        print("\nAnalyzing...\n")

        result = engine.analyze_text(text)

        # Display results
        print("📊 RESULTS:")
        print(f"   Emotion: {result['emotion_primary']} ({result['emotion_confidence']:.1%} confidence)")
        print(f"   Sentiment: {result['sentiment_label']} ({result['sentiment_compound']:+.2f})")

        # Keywords
        import json
        keywords = json.loads(result.get('keywords_json', '[]'))
        if keywords:
            print(f"   Keywords: {', '.join(keywords)}")

        # Mood summary
        summary = engine.text_analyzer.get_mood_summary(result)
        print(f"\n💬 {summary}")

        print("\n" + "-"*65 + "\n")

    print("""
╔═══════════════════════════════════════════════════════════════╗
║                                                                 ║
║  That's the basic text analysis. For full multi-modal magic:   ║
║                                                                 ║
║  1. Record a voice memo (WAV format)                           ║
║  2. Use: engine.analyze(text="...", audio_path="file.wav")    ║
║  3. Watch it detect emotional masking when text/voice disagree ║
║                                                                 ║
║  See examples/basic_usage.py for more!                         ║
║                                                                 ║
╚═══════════════════════════════════════════════════════════════╝
""")

    print("\n✅ Thanks for trying EmpathyEngine!\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!\n")
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        print("Make sure you've installed dependencies: pip install -r requirements.txt\n")
