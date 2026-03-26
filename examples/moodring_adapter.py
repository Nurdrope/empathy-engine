"""
EmpathyEngine - MoodRing Integration Adapter
Demonstrates how MoodRing uses EmpathyEngine
"""

from empathy_engine import EmpathyEngine
from datetime import datetime
import json


class MoodRingAdapter:
    """
    Adapter for integrating EmpathyEngine with MoodRing.

    This shows how MoodRing's database structure maps to EmpathyEngine's
    expected entry format and how results are stored back.
    """

    def __init__(self, database):
        """
        Initialize adapter.

        Args:
            database: MoodRing MoodDatabase instance
        """
        self.engine = EmpathyEngine()
        self.database = database

    def analyze_journal_entry(self, text, audio_path=None):
        """
        Analyze a journal entry (text + optional voice).

        Args:
            text: Journal entry text
            audio_path: Optional path to voice recording

        Returns:
            Dict with analysis results ready for database storage
        """
        # Perform multi-modal analysis
        result = self.engine.analyze(
            text=text,
            audio_path=audio_path
        )

        # Extract data for database storage
        text_analysis = result.get('text_analysis', {})
        voice_analysis = result.get('voice_analysis', {})

        # Build database entry
        entry_data = {
            'timestamp': datetime.now().isoformat(),
            'text': text,
            'entry_type': 'voice' if audio_path else 'text',

            # Sentiment
            'sentiment_label': text_analysis.get('sentiment_label'),
            'sentiment_positive': text_analysis.get('sentiment_positive'),
            'sentiment_negative': text_analysis.get('sentiment_negative'),
            'sentiment_neutral': text_analysis.get('sentiment_neutral'),
            'sentiment_compound': text_analysis.get('sentiment_compound'),

            # Emotion
            'emotion_primary': result.get('primary_emotion'),
            'emotion_confidence': result.get('confidence'),
            'emotions_json': text_analysis.get('emotions_json'),

            # Keywords
            'keywords_json': text_analysis.get('keywords_json'),

            # Fusion metadata
            'fusion_agreement': result.get('agreement'),
            'fusion_authenticity': result.get('authenticity_score'),
            'fusion_notes': result.get('fusion_notes'),
        }

        # Add prosody if voice
        if audio_path:
            entry_data.update({
                'prosody_emotion': voice_analysis.get('prosody_emotion'),
                'prosody_confidence': voice_analysis.get('prosody_confidence'),
                'prosody_pitch': voice_analysis.get('prosody_features', {}).get('pitch_mean'),
                'prosody_energy': voice_analysis.get('prosody_features', {}).get('energy_mean'),
                'prosody_speech_rate': voice_analysis.get('prosody_features', {}).get('speech_rate'),
            })

        return entry_data

    def save_entry(self, text, audio_path=None):
        """
        Analyze and save journal entry to database.

        Args:
            text: Journal entry text
            audio_path: Optional path to voice recording

        Returns:
            Entry ID
        """
        entry_data = self.analyze_journal_entry(text, audio_path)

        # Save to database
        entry_id = self.database.add_entry(**entry_data)

        return entry_id

    def get_patterns(self, days=30):
        """
        Detect patterns from recent entries.

        Args:
            days: Number of days to analyze

        Returns:
            Dict with detected patterns
        """
        # Get recent entries from database
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        db_entries = self.database.get_entries_by_date_range(
            start_date.strftime("%Y-%m-%d %H:%M:%S"),
            end_date.strftime("%Y-%m-%d %H:%M:%S")
        )

        # Convert to EmpathyEngine format
        entries = []
        for db_entry in db_entries:
            entry = {
                'timestamp': db_entry['timestamp'],
                'text': db_entry['text'],
                'emotion_primary': db_entry['emotion_primary'],
                'sentiment_compound': db_entry['sentiment_compound'],
                'keywords_json': db_entry.get('keywords_json'),
            }
            if db_entry.get('prosody_emotion'):
                entry['prosody_emotion'] = db_entry['prosody_emotion']

            entries.append(entry)

        # Detect patterns
        patterns = self.engine.detect_patterns(entries, days=days)

        return patterns

    def analyze_with_context(self, text, audio_path=None, pattern_days=30):
        """
        Analyze entry with historical context.

        Args:
            text: Journal entry text
            audio_path: Optional voice recording
            pattern_days: Days of history to analyze

        Returns:
            Dict with analysis + contextual insights
        """
        # Get historical entries
        end_date = datetime.now()
        start_date = end_date - timedelta(days=pattern_days)

        db_entries = self.database.get_entries_by_date_range(
            start_date.strftime("%Y-%m-%d %H:%M:%S"),
            end_date.strftime("%Y-%m-%d %H:%M:%S")
        )

        # Convert to EmpathyEngine format
        entries = []
        for db_entry in db_entries:
            entry = {
                'timestamp': db_entry['timestamp'],
                'text': db_entry['text'],
                'emotion_primary': db_entry['emotion_primary'],
                'sentiment_compound': db_entry['sentiment_compound'],
                'keywords_json': db_entry.get('keywords_json'),
            }
            if db_entry.get('prosody_emotion'):
                entry['prosody_emotion'] = db_entry['prosody_emotion']

            entries.append(entry)

        # Analyze with context
        result = self.engine.analyze_with_context(
            text=text,
            audio_path=audio_path,
            entries=entries,
            pattern_days=pattern_days
        )

        return result


# Example usage
if __name__ == "__main__":
    # Simulated MoodRing database
    class MockDatabase:
        def __init__(self):
            self.entries = []

        def add_entry(self, **kwargs):
            entry_id = len(self.entries) + 1
            entry = {'id': entry_id, **kwargs}
            self.entries.append(entry)
            return entry_id

        def get_entries_by_date_range(self, start, end):
            return self.entries

    print("🔗 MOODRING ADAPTER EXAMPLE\n")

    # Create mock database and adapter
    db = MockDatabase()
    adapter = MoodRingAdapter(db)

    # Add some entries
    print("Adding journal entries...")
    adapter.save_entry("I'm feeling stressed about work today")
    adapter.save_entry("Really anxious about the meeting tomorrow")
    adapter.save_entry("Feeling a bit better after talking to a friend")

    print(f"✅ Saved {len(db.entries)} entries\n")

    # Detect patterns
    print("Detecting patterns...")
    patterns = adapter.get_patterns(days=30)

    anxiety = patterns.get('anxiety_spikes', {})
    if anxiety.get('detected'):
        print(f"⚠️  Anxiety spikes detected: {anxiety['spike_count']}")
        print(f"   {anxiety['recommendation']}")

    print("\n✅ Adapter example complete!")
