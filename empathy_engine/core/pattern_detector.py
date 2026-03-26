"""
EmpathyEngine - Emotional Pattern Detection
Detect cycles, spikes, and trends in emotional data

Extracted from MoodRing (Nov 2025)
Generalized for use with any data source
"""

import json
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from typing import List, Dict, Optional
import numpy as np
from ..utils.time import parse_iso_timestamp


class PatternDetector:
    """
    Analyzes historical emotional data to detect patterns:
    - Anxiety spikes
    - Low-energy periods
    - Overthinking cycles
    - Mood swings
    - Time-of-day patterns
    - Weekly patterns

    Expects data entries in format:
    {
        'timestamp': ISO format datetime string,
        'text': entry text,
        'emotion_primary': emotion label,
        'sentiment_compound': -1 to 1 sentiment score,
        'keywords_json': JSON string of keywords,
        'prosody_emotion': optional voice emotion
    }
    """

    def __init__(self, entries: Optional[List[Dict]] = None):
        """
        Initialize pattern detector.

        Args:
            entries: Optional list of emotional data entries
        """
        self.entries = entries or []

    def set_entries(self, entries: List[Dict]):
        """Set or update entries for analysis."""
        self.entries = entries

    def detect_all_patterns(self, days: int = 30) -> Dict:
        """
        Run all pattern detection algorithms.

        Args:
            days: number of days to analyze (filters entries)

        Returns:
            dict with all detected patterns
        """
        if not self.entries:
            return {'message': 'No data available for pattern detection'}

        # Filter entries by date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        filtered_entries = []
        for entry in self.entries:
            ts = parse_iso_timestamp(entry.get('timestamp'))
            if ts and ts >= start_date:
                filtered_entries.append(entry)

        if not filtered_entries:
            return {'message': 'Not enough data for pattern detection'}

        patterns = {}
        patterns['anxiety_spikes'] = self.detect_anxiety_spikes(filtered_entries)
        patterns['low_energy'] = self.detect_low_energy_periods(filtered_entries)
        patterns['overthinking'] = self.detect_overthinking(filtered_entries)
        patterns['mood_swings'] = self.detect_mood_swings(filtered_entries)
        patterns['time_patterns'] = self.detect_time_of_day_patterns(filtered_entries)
        patterns['weekly_patterns'] = self.detect_weekly_patterns(filtered_entries)

        return patterns

    def detect_anxiety_spikes(self, entries: List[Dict]) -> Dict:
        """
        Detect anxiety spikes and cycles.

        Args:
            entries: List of entry dicts

        Returns:
            dict with spike info and recommendations
        """
        anxiety_scores = []
        timestamps = []

        for entry in entries:
            # Anxiety indicators
            emotion = entry.get('emotion_primary', '')
            sentiment = entry.get('sentiment_compound', 0)
            keywords_json = entry.get('keywords_json')

            # Calculate anxiety score
            anxiety_score = 0

            if emotion in ['fear', 'anxiety']:
                anxiety_score += 0.5

            if sentiment < -0.3:
                anxiety_score += abs(sentiment) * 0.3

            # Check keywords for anxiety markers
            if keywords_json:
                try:
                    keywords = json.loads(keywords_json)
                    anxiety_words = ['worry', 'anxious', 'nervous', 'stress', 'afraid', 'scared', 'panic']
                    for keyword in keywords:
                        if any(word in keyword.lower() for word in anxiety_words):
                            anxiety_score += 0.2
                except:
                    pass

            if anxiety_score > 0:
                anxiety_scores.append(anxiety_score)
                ts = parse_iso_timestamp(entry.get('timestamp'))
                if ts:
                    timestamps.append(ts)

        if not anxiety_scores:
            return {'detected': False, 'message': 'No anxiety patterns detected'}

        # Detect spikes (above threshold)
        threshold = np.mean(anxiety_scores) + np.std(anxiety_scores)
        spikes = []

        for i, score in enumerate(anxiety_scores):
            if score > threshold:
                spikes.append({
                    'date': timestamps[i].strftime("%Y-%m-%d %H:%M"),
                    'score': round(score, 2)
                })

        # Detect cycles
        high_anxiety_days = [t.date() for t, s in zip(timestamps, anxiety_scores) if s > 0.5]
        if len(high_anxiety_days) >= 3:
            day_counts = Counter(high_anxiety_days)
            cycle_detected = len([c for c in day_counts.values() if c > 1]) > 0
        else:
            cycle_detected = False

        return {
            'detected': len(spikes) > 0,
            'spike_count': len(spikes),
            'spikes': spikes[:5],
            'avg_anxiety': round(np.mean(anxiety_scores), 2),
            'cycle_detected': cycle_detected,
            'recommendation': self._get_anxiety_recommendation(len(spikes), cycle_detected)
        }

    def detect_low_energy_periods(self, entries: List[Dict]) -> Dict:
        """
        Detect sustained low-energy periods.

        Args:
            entries: List of entry dicts

        Returns:
            dict with low-energy period info
        """
        daily_energy = defaultdict(list)

        for entry in entries:
            ts = parse_iso_timestamp(entry.get('timestamp'))
            if not ts:
                continue
            date = ts.date()
            sentiment = entry.get('sentiment_compound', 0)
            emotion = entry.get('emotion_primary', '')

            # Energy score
            energy_score = sentiment

            # Adjust for specific emotions
            if emotion in ['sadness', 'sad']:
                energy_score -= 0.3
            elif emotion in ['joy', 'excitement']:
                energy_score += 0.2

            daily_energy[date].append(energy_score)

        # Calculate daily averages
        daily_avg = {date: np.mean(scores) for date, scores in daily_energy.items()}

        # Find consecutive low-energy days
        sorted_dates = sorted(daily_avg.keys())
        low_energy_periods = []
        current_period = []

        for date in sorted_dates:
            if daily_avg[date] < -0.2:
                current_period.append(date)
            else:
                if len(current_period) >= 2:
                    low_energy_periods.append({
                        'start': str(current_period[0]),
                        'end': str(current_period[-1]),
                        'duration': len(current_period),
                        'avg_energy': round(np.mean([daily_avg[d] for d in current_period]), 2)
                    })
                current_period = []

        if len(current_period) >= 2:
            low_energy_periods.append({
                'start': str(current_period[0]),
                'end': str(current_period[-1]),
                'duration': len(current_period),
                'avg_energy': round(np.mean([daily_avg[d] for d in current_period]), 2)
            })

        return {
            'detected': len(low_energy_periods) > 0,
            'period_count': len(low_energy_periods),
            'periods': low_energy_periods,
            'recommendation': self._get_low_energy_recommendation(low_energy_periods)
        }

    def detect_overthinking(self, entries: List[Dict]) -> Dict:
        """
        Detect overthinking patterns from entry length and keyword density.

        Args:
            entries: List of entry dicts

        Returns:
            dict with overthinking indicators
        """
        entry_lengths = []
        rumination_scores = []

        for entry in entries:
            text = entry.get('text', '')
            text_length = len(text.split())

            if text_length > 100:
                entry_lengths.append(text_length)

            keywords_json = entry.get('keywords_json')
            if keywords_json:
                try:
                    keywords = json.loads(keywords_json)
                    rumination_words = ['why', 'should', 'if', 'maybe', 'what if', 'worry', 'think', 'thought']
                    rumination_count = sum(1 for kw in keywords if any(word in kw.lower() for word in rumination_words))

                    if rumination_count > 2:
                        rumination_scores.append(rumination_count)
                except:
                    pass

        overthinking_detected = (
            len(entry_lengths) > 5 and np.mean(entry_lengths) > 150
        ) or len(rumination_scores) > 3

        return {
            'detected': overthinking_detected,
            'long_entry_count': len(entry_lengths),
            'avg_entry_length': round(np.mean(entry_lengths), 1) if entry_lengths else 0,
            'rumination_instances': len(rumination_scores),
            'recommendation': self._get_overthinking_recommendation(overthinking_detected)
        }

    def detect_mood_swings(self, entries: List[Dict]) -> Dict:
        """
        Detect rapid mood changes (volatility).

        Args:
            entries: List of entry dicts

        Returns:
            dict with mood swing info
        """
        sentiments = []
        timestamps = []

        for entry in entries:
            sentiment = entry.get('sentiment_compound')
            if sentiment is not None:
                sentiments.append(sentiment)
                ts = parse_iso_timestamp(entry.get('timestamp'))
                if ts:
                    timestamps.append(ts)

        if len(sentiments) < 2:
            return {'detected': False, 'message': 'Not enough data'}

        # Calculate changes between consecutive entries
        sentiment_changes = []
        for i in range(1, len(sentiments)):
            change = abs(sentiments[i] - sentiments[i-1])
            time_diff = (timestamps[i] - timestamps[i-1]).total_seconds() / 3600

            if change > 0.5 and time_diff < 6:
                sentiment_changes.append({
                    'from': round(sentiments[i-1], 2),
                    'to': round(sentiments[i], 2),
                    'change': round(change, 2),
                    'time': timestamps[i].strftime("%Y-%m-%d %H:%M")
                })

        volatility = np.std(sentiments) if sentiments else 0

        return {
            'detected': len(sentiment_changes) > 0,
            'swing_count': len(sentiment_changes),
            'swings': sentiment_changes[:5],
            'volatility': round(volatility, 2),
            'recommendation': self._get_mood_swing_recommendation(volatility)
        }

    def detect_time_of_day_patterns(self, entries: List[Dict]) -> Dict:
        """
        Detect patterns based on time of day.

        Args:
            entries: List of entry dicts

        Returns:
            dict with time-based insights
        """
        time_moods = defaultdict(list)

        for entry in entries:
            timestamp = parse_iso_timestamp(entry.get('timestamp'))
            if not timestamp:
                continue
            hour = timestamp.hour
            sentiment = entry.get('sentiment_compound', 0)

            if 6 <= hour < 12:
                time_period = 'morning'
            elif 12 <= hour < 17:
                time_period = 'afternoon'
            elif 17 <= hour < 21:
                time_period = 'evening'
            else:
                time_period = 'night'

            time_moods[time_period].append(sentiment)

        time_averages = {
            period: round(np.mean(sentiments), 2)
            for period, sentiments in time_moods.items()
            if sentiments
        }

        if time_averages:
            best_time = max(time_averages.items(), key=lambda x: x[1])
            worst_time = min(time_averages.items(), key=lambda x: x[1])
        else:
            best_time = worst_time = None

        return {
            'detected': len(time_averages) > 0,
            'time_averages': time_averages,
            'best_time': best_time[0] if best_time else None,
            'worst_time': worst_time[0] if worst_time else None,
            'recommendation': self._get_time_recommendation(best_time, worst_time)
        }

    def detect_weekly_patterns(self, entries: List[Dict]) -> Dict:
        """
        Detect patterns based on day of week.

        Args:
            entries: List of entry dicts

        Returns:
            dict with weekly patterns
        """
        day_moods = defaultdict(list)

        for entry in entries:
            timestamp = parse_iso_timestamp(entry.get('timestamp'))
            if not timestamp:
                continue
            day_name = timestamp.strftime('%A')
            sentiment = entry.get('sentiment_compound', 0)

            day_moods[day_name].append(sentiment)

        day_averages = {
            day: round(np.mean(sentiments), 2)
            for day, sentiments in day_moods.items()
            if sentiments
        }

        if day_averages:
            best_day = max(day_averages.items(), key=lambda x: x[1])
            worst_day = min(day_averages.items(), key=lambda x: x[1])
        else:
            best_day = worst_day = None

        return {
            'detected': len(day_averages) > 0,
            'day_averages': day_averages,
            'best_day': best_day[0] if best_day else None,
            'worst_day': worst_day[0] if worst_day else None,
            'recommendation': self._get_weekly_recommendation(best_day, worst_day)
        }

    # Recommendation generators
    def _get_anxiety_recommendation(self, spike_count: int, cycle_detected: bool) -> str:
        if spike_count == 0:
            return "No anxiety spikes detected. Keep up the good work!"
        if cycle_detected:
            return "Recurring anxiety pattern detected. Consider: tracking triggers, regular breathing exercises, professional support."
        elif spike_count > 3:
            return "Multiple anxiety spikes detected. Try: daily meditation, anxiety journaling, identifying stressors."
        else:
            return "Occasional anxiety detected. Practice: grounding techniques, mindful breathing when spikes occur."

    def _get_low_energy_recommendation(self, periods: List[Dict]) -> str:
        if not periods:
            return "Energy levels seem stable!"
        longest = max(periods, key=lambda x: x['duration'])
        if longest['duration'] > 5:
            return f"Extended low-energy period detected ({longest['duration']} days). Consider: sleep hygiene, exercise, nutrition, talking to someone."
        else:
            return "Some low-energy days detected. Try: morning sunlight, movement, hydration, gentle self-care."

    def _get_overthinking_recommendation(self, detected: bool) -> str:
        if not detected:
            return "No overthinking patterns detected."
        return "Overthinking pattern detected. Try: time-boxing worries, 'thought dumping', meditation, physical activity to break rumination loops."

    def _get_mood_swing_recommendation(self, volatility: float) -> str:
        if volatility < 0.3:
            return "Mood is relatively stable."
        elif volatility < 0.6:
            return "Moderate mood fluctuations. Consider: consistent routines, mood tracking, identifying triggers."
        else:
            return "High mood volatility detected. Try: routine stability, avoiding extreme stressors, grounding practices, professional support."

    def _get_time_recommendation(self, best_time: Optional[tuple], worst_time: Optional[tuple]) -> str:
        if not best_time or not worst_time:
            return "Not enough data for time-based insights."
        return f"You tend to feel best in the {best_time[0]} ({best_time[1]:+.2f}) and worst in the {worst_time[0]} ({worst_time[1]:+.2f}). Schedule important tasks during your high-energy times."

    def _get_weekly_recommendation(self, best_day: Optional[tuple], worst_day: Optional[tuple]) -> str:
        if not best_day or not worst_day:
            return "Not enough data for weekly patterns."
        return f"You tend to feel best on {best_day[0]}s ({best_day[1]:+.2f}) and worst on {worst_day[0]}s ({worst_day[1]:+.2f}). Plan self-care for challenging days."
