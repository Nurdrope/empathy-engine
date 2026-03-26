"""
EmpathyEngine - Summary Generation Module
Generates daily, weekly, and monthly emotional summaries from entry data

Extracted and adapted from MoodRing (Dec 2025)
"""

import json
from datetime import datetime, timedelta
from collections import Counter
from typing import List, Dict, Optional
from ..utils.time import parse_iso_timestamp


class SummaryGenerator:
    """
    Generates emotional summaries from historical entry data.

    Can create:
    - Daily summaries (single day overview)
    - Weekly summaries (7-day trends)
    - Monthly summaries (full month analysis)

    Works with generic entry dicts (no database dependency).

    Usage:
        generator = SummaryGenerator()
        summary = generator.generate_daily(entries)
        summary = generator.generate_monthly(entries)
    """

    def __init__(self):
        pass

    def generate_daily(
        self,
        entries: List[Dict],
        date: Optional[datetime] = None
    ) -> Dict:
        """
        Generate summary for a specific day.

        Args:
            entries: List of entry dicts with timestamp, emotion, sentiment, keywords
            date: Target date (None = today). Filters entries to this date only.

        Returns:
            Dict with:
            - date: summary date (YYYY-MM-DD)
            - entry_count: number of entries
            - dominant_emotion: most common emotion
            - sentiment_avg: average sentiment compound score
            - keywords: most common keywords
            - tone_summary: description of overall tone
            - emotions_distribution: breakdown of all emotions
        """
        if date is None:
            date = datetime.now()

        # Filter entries to this specific day
        start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)

        day_entries = []
        for entry in entries:
            ts = parse_iso_timestamp(entry.get('timestamp'))
            if ts and start_date <= ts < end_date:
                day_entries.append(entry)

        if not day_entries:
            return {
                'date': start_date.strftime("%Y-%m-%d"),
                'entry_count': 0,
                'dominant_emotion': None,
                'sentiment_avg': 0,
                'keywords': [],
                'tone_summary': 'No entries for this day',
                'emotions_distribution': {}
            }

        # Collect data
        emotions = []
        prosody_emotions = []
        sentiments = []
        all_keywords = []

        for entry in day_entries:
            # Emotions
            if entry.get('emotion_primary'):
                emotions.append(entry['emotion_primary'])

            # Prosody emotions (voice)
            if entry.get('prosody_emotion'):
                prosody_emotions.append(entry['prosody_emotion'])

            # Sentiments
            if entry.get('sentiment_compound') is not None:
                sentiments.append(entry['sentiment_compound'])

            # Keywords
            keywords_json = entry.get('keywords_json')
            if keywords_json:
                try:
                    keywords = json.loads(keywords_json) if isinstance(keywords_json, str) else keywords_json
                    all_keywords.extend(keywords)
                except:
                    pass

        # Calculate statistics
        dominant_emotion = None
        if emotions:
            emotion_counts = Counter(emotions)
            dominant_emotion = emotion_counts.most_common(1)[0][0]

        sentiment_avg = sum(sentiments) / len(sentiments) if sentiments else 0

        # Top keywords
        if all_keywords:
            keyword_counts = Counter(all_keywords)
            top_keywords = [kw for kw, count in keyword_counts.most_common(5)]
        else:
            top_keywords = []

        # Emotions distribution
        emotions_distribution = dict(Counter(emotions))

        # Tone summary
        tone_summary = self._generate_tone_description(
            sentiment_avg,
            dominant_emotion,
            prosody_emotions,
            len(day_entries)
        )

        return {
            'date': start_date.strftime("%Y-%m-%d"),
            'entry_count': len(day_entries),
            'dominant_emotion': dominant_emotion,
            'sentiment_avg': round(sentiment_avg, 3),
            'keywords': top_keywords,
            'tone_summary': tone_summary,
            'emotions_distribution': emotions_distribution,
            'prosody_emotions': prosody_emotions
        }

    def generate_weekly(
        self,
        entries: List[Dict],
        end_date: Optional[datetime] = None
    ) -> Dict:
        """
        Generate summary for a 7-day week ending on end_date.

        Args:
            entries: List of entry dicts
            end_date: End of week (None = today). Week is 7 days ending on this date.

        Returns:
            Dict with weekly statistics and trends
        """
        if end_date is None:
            end_date = datetime.now()

        start_date = end_date - timedelta(days=7)

        # Filter entries to this week
        week_entries = []
        for entry in entries:
            ts = parse_iso_timestamp(entry.get('timestamp'))
            if ts and start_date <= ts <= end_date:
                week_entries.append(entry)

        if not week_entries:
            return {
                'period': f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
                'entry_count': 0,
                'summary': 'No entries for this week'
            }

        # Analyze entries
        emotions = []
        prosody_emotions = []
        sentiments = []
        all_keywords = []
        daily_counts = Counter()

        for entry in week_entries:
            timestamp = parse_iso_timestamp(entry.get('timestamp'))
            if not timestamp:
                continue
            entry_date = timestamp.date()
            daily_counts[entry_date.strftime("%Y-%m-%d")] += 1

            if entry.get('emotion_primary'):
                emotions.append(entry['emotion_primary'])

            if entry.get('prosody_emotion'):
                prosody_emotions.append(entry['prosody_emotion'])

            if entry.get('sentiment_compound') is not None:
                sentiments.append(entry['sentiment_compound'])

            keywords_json = entry.get('keywords_json')
            if keywords_json:
                try:
                    keywords = json.loads(keywords_json) if isinstance(keywords_json, str) else keywords_json
                    all_keywords.extend(keywords)
                except:
                    pass

        # Calculate statistics
        emotion_distribution = dict(Counter(emotions))
        prosody_distribution = dict(Counter(prosody_emotions))
        sentiment_avg = sum(sentiments) / len(sentiments) if sentiments else 0
        sentiment_min = min(sentiments) if sentiments else 0
        sentiment_max = max(sentiments) if sentiments else 0

        # Top keywords
        keyword_counts = Counter(all_keywords)
        top_keywords = [kw for kw, count in keyword_counts.most_common(10)]

        # Most active day
        most_active_day = daily_counts.most_common(1)[0] if daily_counts else (None, 0)

        # Generate narrative
        summary_text = self._generate_period_narrative(
            len(week_entries),
            sentiment_avg,
            emotion_distribution,
            prosody_distribution,
            top_keywords,
            'week'
        )

        return {
            'period': f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
            'period_type': 'weekly',
            'entry_count': len(week_entries),
            'sentiment_avg': round(sentiment_avg, 3),
            'sentiment_range': (round(sentiment_min, 3), round(sentiment_max, 3)),
            'emotion_distribution': emotion_distribution,
            'prosody_distribution': prosody_distribution,
            'top_keywords': top_keywords,
            'most_active_day': most_active_day[0] if most_active_day[0] else None,
            'most_active_day_count': most_active_day[1] if most_active_day[0] else 0,
            'summary': summary_text
        }

    def generate_monthly(
        self,
        entries: List[Dict],
        year: Optional[int] = None,
        month: Optional[int] = None
    ) -> Dict:
        """
        Generate summary for an entire month.

        Args:
            entries: List of entry dicts
            year: Year (None = current year)
            month: Month 1-12 (None = current month)

        Returns:
            Dict with monthly statistics and trends
        """
        if year is None or month is None:
            now = datetime.now()
            year = now.year
            month = now.month

        # Get date range for month
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)

        # Filter entries to this month
        month_entries = []
        for entry in entries:
            ts = parse_iso_timestamp(entry.get('timestamp'))
            if ts and start_date <= ts < end_date:
                month_entries.append(entry)

        if not month_entries:
            return {
                'month': f"{year}-{month:02d}",
                'entry_count': 0,
                'summary': 'No entries for this month'
            }

        # Analyze all entries
        emotions = []
        prosody_emotions = []
        sentiments = []
        all_keywords = []
        daily_counts = Counter()

        for entry in month_entries:
            timestamp = parse_iso_timestamp(entry.get('timestamp'))
            if not timestamp:
                continue
            entry_date = timestamp.date()
            daily_counts[entry_date.strftime("%Y-%m-%d")] += 1

            if entry.get('emotion_primary'):
                emotions.append(entry['emotion_primary'])

            if entry.get('prosody_emotion'):
                prosody_emotions.append(entry['prosody_emotion'])

            if entry.get('sentiment_compound') is not None:
                sentiments.append(entry['sentiment_compound'])

            keywords_json = entry.get('keywords_json')
            if keywords_json:
                try:
                    keywords = json.loads(keywords_json) if isinstance(keywords_json, str) else keywords_json
                    all_keywords.extend(keywords)
                except:
                    pass

        # Calculate statistics
        emotion_distribution = dict(Counter(emotions))
        prosody_distribution = dict(Counter(prosody_emotions))
        sentiment_avg = sum(sentiments) / len(sentiments) if sentiments else 0
        sentiment_min = min(sentiments) if sentiments else 0
        sentiment_max = max(sentiments) if sentiments else 0

        # Top keywords
        keyword_counts = Counter(all_keywords)
        top_keywords = [kw for kw, count in keyword_counts.most_common(10)]

        # Most active day
        most_active_day = daily_counts.most_common(1)[0] if daily_counts else (None, 0)

        # Generate narrative summary
        summary_text = self._generate_period_narrative(
            len(month_entries),
            sentiment_avg,
            emotion_distribution,
            prosody_distribution,
            top_keywords,
            'month'
        )

        return {
            'month': f"{year}-{month:02d}",
            'period_type': 'monthly',
            'entry_count': len(month_entries),
            'sentiment_avg': round(sentiment_avg, 3),
            'sentiment_range': (round(sentiment_min, 3), round(sentiment_max, 3)),
            'emotion_distribution': emotion_distribution,
            'prosody_distribution': prosody_distribution,
            'top_keywords': top_keywords,
            'most_active_day': most_active_day[0] if most_active_day[0] else None,
            'most_active_day_count': most_active_day[1] if most_active_day[0] else 0,
            'summary': summary_text
        }

    def _generate_tone_description(
        self,
        sentiment_avg: float,
        dominant_emotion: Optional[str],
        prosody_emotions: List[str],
        entry_count: int
    ) -> str:
        """Generate human-readable tone description for a day."""
        parts = []

        # Entry count
        if entry_count == 1:
            parts.append("One entry")
        else:
            parts.append(f"{entry_count} entries")

        # Sentiment
        if sentiment_avg >= 0.3:
            parts.append("mostly positive")
        elif sentiment_avg <= -0.3:
            parts.append("mostly negative")
        else:
            parts.append("neutral")

        # Dominant emotion
        if dominant_emotion:
            parts.append(f"feeling {dominant_emotion}")

        # Voice tone (if any voice entries)
        if prosody_emotions:
            most_common_tone = Counter(prosody_emotions).most_common(1)[0][0]
            parts.append(f"voice: {most_common_tone}")

        return " | ".join(parts)

    def _generate_period_narrative(
        self,
        entry_count: int,
        sentiment_avg: float,
        emotions: Dict,
        prosody: Dict,
        keywords: List[str],
        period_type: str = 'week'
    ) -> str:
        """Generate narrative summary for a time period."""
        lines = []

        # Overall stats
        lines.append(f"Total entries: {entry_count}")

        # Sentiment
        if sentiment_avg >= 0.3:
            mood_desc = "positive and upbeat"
        elif sentiment_avg >= 0.1:
            mood_desc = "generally positive"
        elif sentiment_avg <= -0.3:
            mood_desc = "challenging and difficult"
        elif sentiment_avg <= -0.1:
            mood_desc = "somewhat negative"
        else:
            mood_desc = "neutral and balanced"

        lines.append(f"Overall mood: {mood_desc} (avg sentiment: {sentiment_avg:.2f})")

        # Dominant emotions
        if emotions:
            emotion_list = [f"{emotion} ({count})" for emotion, count in
                          sorted(emotions.items(), key=lambda x: x[1], reverse=True)[:3]]
            lines.append(f"Emotions: {', '.join(emotion_list)}")

        # Voice tones (if any)
        if prosody:
            tone_list = [f"{tone} ({count})" for tone, count in
                        sorted(prosody.items(), key=lambda x: x[1], reverse=True)[:3]]
            lines.append(f"Voice tones: {', '.join(tone_list)}")

        # Key themes
        if keywords:
            lines.append(f"Key themes: {', '.join(keywords[:5])}")

        return "\n".join(lines)
