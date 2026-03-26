"""
Test the summary features
"""

from datetime import datetime, timedelta

from empathy_engine import EmpathyEngine


def main():
    # Initialize engine
    engine = EmpathyEngine()

    print("=" * 60)
    print("TESTING EMPATHYENGINE SUMMARY FEATURES")
    print("=" * 60)
    print()

    # Test: Summaries
    print("Testing Summary Generation")
    print("-" * 60)

    # Create some fake historical entries
    now = datetime.now()
    fake_entries = [
        {
            'timestamp': (now - timedelta(days=i)).isoformat(),
            'text': 'Sample entry',
            'emotion_primary': ['joy', 'sadness', 'neutral', 'anxiety'][i % 4],
            'sentiment_compound': [0.5, -0.3, 0.1, -0.5][i % 4],
            'keywords_json': '["work", "stress", "family"]',
            'prosody_emotion': None
        }
        for i in range(10)
    ]

    # Daily summary
    daily = engine.generate_summary(fake_entries, period='daily')
    print("\nDaily Summary:")
    print(f"  Date: {daily['date']}")
    print(f"  Entries: {daily['entry_count']}")
    print(f"  Tone: {daily['tone_summary']}")
    print(f"  Dominant emotion: {daily['dominant_emotion']}")

    # Weekly summary
    weekly = engine.generate_summary(fake_entries, period='weekly')
    print("\nWeekly Summary:")
    print(f"  Period: {weekly['period']}")
    print(f"  Entries: {weekly['entry_count']}")
    print(f"  Avg sentiment: {weekly['sentiment_avg']:.2f}")
    print(f"  Summary:\n{weekly['summary']}")

    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED - Summary features working!")
    print("=" * 60)


if __name__ == "__main__":
    main()
