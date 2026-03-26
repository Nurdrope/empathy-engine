"""
EmpathyEngine - Emotional Baseline Profiler
Learns a user's "normal" emotional state to detect deviations

This module builds a profile of a user's typical emotional patterns:
- Baseline sentiment range
- Common emotions
- Typical voice prosody
- Daily/weekly patterns
- Typical intensity levels

Then compares new entries against baseline to detect:
- Unusual emotions (not in their normal range)
- Sentiment shifts (more positive/negative than usual)
- Abnormal intensity (unusually strong/weak)
- Pattern breaks (different from their routine)

Created: December 18, 2025
Part of the "all of them" expansion
"""

import json
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple
from collections import Counter
import numpy as np
from ..utils.time import parse_iso_timestamp


class BaselineProfiler:
    """
    Builds and maintains an emotional baseline profile for a user.

    The baseline represents a user's "normal" emotional state.
    Deviations from baseline can indicate:
    - Positive changes (improvement in mood)
    - Negative changes (decline in well-being)
    - Situational reactions (events triggering unusual emotions)
    - Growth/change in emotional patterns

    Usage:
        profiler = BaselineProfiler()

        # Build baseline from historical data (needs 14+ days, 20+ entries)
        baseline = profiler.build_baseline(historical_entries)

        # Compare new entry to baseline
        deviation = profiler.compare_to_baseline(analysis_result, baseline)
        # Returns: {'is_deviation': True, 'severity': 0.65, 'dimensions': [...]}
    """

    def __init__(self):
        # Minimum data requirements for reliable baseline
        self.min_days = 14
        self.min_entries = 20

    def build_baseline(
        self,
        entries: List[Dict],
        days: Optional[int] = None,
        user_id: Optional[str] = None
    ) -> Dict:
        """
        Build emotional baseline from historical entries.

        Args:
            entries: List of historical entry dicts
            days: Number of days to include (None = all entries)
            user_id: Optional user identifier

        Returns:
            Dict with baseline profile:
            - sentiment: mean, std, range
            - emotions: frequency distribution
            - prosody: voice baseline (if available)
            - intensity: typical intensity range
            - time_patterns: hourly/daily patterns
            - entry_frequency: how often user journals
            - metadata: user_id, date range, entry count
        """
        if not entries:
            return self._empty_baseline(user_id)

        # Filter by time window if specified
        if days:
            cutoff = datetime.now() - timedelta(days=days)
            filtered = []
            for entry in entries:
                ts = parse_iso_timestamp(entry.get('timestamp'))
                if ts and ts >= cutoff:
                    filtered.append(entry)
            entries = filtered

        # Check if we have enough data
        if len(entries) < self.min_entries:
            return self._insufficient_data_baseline(user_id, len(entries))

        # Calculate baseline dimensions
        baseline = {
            'sentiment': self._calculate_sentiment_baseline(entries),
            'emotions': self._calculate_emotion_baseline(entries),
            'prosody': self._calculate_prosody_baseline(entries),
            'intensity': self._calculate_intensity_baseline(entries),
            'time_patterns': self._calculate_time_patterns(entries),
            'entry_frequency': self._calculate_entry_frequency(entries),
            'keywords': self._calculate_keyword_baseline(entries),
            'metadata': {
                'user_id': user_id,
                'entry_count': len(entries),
                'date_range': self._get_date_range(entries),
                'baseline_created': datetime.now().isoformat(),
                'sufficient_data': True
            }
        }

        return baseline

    def compare_to_baseline(
        self,
        analysis_result: Dict,
        baseline: Dict
    ) -> Dict:
        """
        Compare current analysis to baseline profile.

        Args:
            analysis_result: Output from EmpathyEngine.analyze()
            baseline: Output from build_baseline()

        Returns:
            Dict with:
            - is_deviation: bool
            - severity: float 0-1 (how far from baseline)
            - dimensions: List of specific deviations detected
            - interpretation: Human-readable explanation
        """
        if not baseline.get('metadata', {}).get('sufficient_data'):
            return self._insufficient_baseline()

        deviations = []
        deviation_scores = []

        # Compare sentiment
        sentiment_dev = self._compare_sentiment(analysis_result, baseline)
        if sentiment_dev:
            deviations.append(sentiment_dev)
            deviation_scores.append(sentiment_dev['score'])

        # Compare emotion
        emotion_dev = self._compare_emotion(analysis_result, baseline)
        if emotion_dev:
            deviations.append(emotion_dev)
            deviation_scores.append(emotion_dev['score'])

        # Compare intensity (if available)
        if 'intensity' in analysis_result:
            intensity_dev = self._compare_intensity(analysis_result, baseline)
            if intensity_dev:
                deviations.append(intensity_dev)
                deviation_scores.append(intensity_dev['score'])

        # Compare prosody (if available)
        if analysis_result.get('voice_analysis'):
            prosody_dev = self._compare_prosody(analysis_result, baseline)
            if prosody_dev:
                deviations.append(prosody_dev)
                deviation_scores.append(prosody_dev['score'])

        # Calculate overall severity
        severity = max(deviation_scores) if deviation_scores else 0.0

        # Determine if significant deviation (threshold: 0.4)
        is_deviation = severity >= 0.4

        # Generate interpretation
        interpretation = self._generate_interpretation(deviations, severity)

        return {
            'is_deviation': is_deviation,
            'severity': round(severity, 3),
            'dimensions': deviations,
            'interpretation': interpretation,
            'timestamp': datetime.now().isoformat()
        }

    def _calculate_sentiment_baseline(self, entries: List[Dict]) -> Dict:
        """Calculate baseline sentiment statistics."""
        sentiments = [e.get('sentiment_compound', 0) for e in entries]
        sentiments = [s for s in sentiments if s is not None]

        if not sentiments:
            return {'mean': 0, 'std': 0, 'range': (0, 0)}

        return {
            'mean': round(float(np.mean(sentiments)), 3),
            'std': round(float(np.std(sentiments)), 3),
            'range': (round(float(np.min(sentiments)), 3), round(float(np.max(sentiments)), 3)),
            'median': round(float(np.median(sentiments)), 3)
        }

    def _calculate_emotion_baseline(self, entries: List[Dict]) -> Dict:
        """Calculate baseline emotion distribution."""
        emotions = [e.get('emotion_primary') for e in entries if e.get('emotion_primary')]

        if not emotions:
            return {'distribution': {}, 'most_common': None}

        emotion_counts = Counter(emotions)
        total = len(emotions)

        # Convert to percentages
        distribution = {
            emotion: round(count / total, 3)
            for emotion, count in emotion_counts.items()
        }

        most_common = emotion_counts.most_common(1)[0][0]

        return {
            'distribution': distribution,
            'most_common': most_common,
            'variety': len(emotion_counts)  # How many different emotions expressed
        }

    def _calculate_prosody_baseline(self, entries: List[Dict]) -> Optional[Dict]:
        """Calculate baseline voice prosody (if available)."""
        prosody_emotions = [e.get('prosody_emotion') for e in entries if e.get('prosody_emotion')]

        if not prosody_emotions:
            return None

        prosody_counts = Counter(prosody_emotions)
        total = len(prosody_emotions)

        distribution = {
            tone: round(count / total, 3)
            for tone, count in prosody_counts.items()
        }

        return {
            'distribution': distribution,
            'most_common': prosody_counts.most_common(1)[0][0],
            'voice_entry_rate': round(len(prosody_emotions) / len(entries), 3)
        }

    def _calculate_intensity_baseline(self, entries: List[Dict]) -> Dict:
        """
        Calculate typical intensity range.

        Note: Requires entries to have 'intensity' field (from IntensityCalibrator).
        If not available, estimates from sentiment magnitude.
        """
        # Try to use intensity field if available
        intensities = [e.get('intensity') for e in entries if e.get('intensity') is not None]

        if not intensities:
            # Fallback: estimate from sentiment magnitude
            intensities = [abs(e.get('sentiment_compound', 0)) for e in entries]

        if not intensities:
            return {'mean': 0.5, 'std': 0.2, 'range': (0, 1)}

        return {
            'mean': round(float(np.mean(intensities)), 3),
            'std': round(float(np.std(intensities)), 3),
            'range': (round(float(np.min(intensities)), 3), round(float(np.max(intensities)), 3))
        }

    def _calculate_time_patterns(self, entries: List[Dict]) -> Dict:
        """Calculate when user typically journals."""
        hours = []
        days_of_week = []

        for entry in entries:
            dt = parse_iso_timestamp(entry.get('timestamp'))
            if not dt:
                continue
            hours.append(dt.hour)
            days_of_week.append(dt.weekday())  # 0=Monday, 6=Sunday

        hour_counts = Counter(hours)
        day_counts = Counter(days_of_week)

        # Find most common journaling times
        most_common_hour = hour_counts.most_common(1)[0][0] if hour_counts else None
        most_common_day = day_counts.most_common(1)[0][0] if day_counts else None

        return {
            'peak_hour': most_common_hour,
            'peak_day': most_common_day,
            'hour_distribution': dict(hour_counts),
            'day_distribution': dict(day_counts)
        }

    def _calculate_entry_frequency(self, entries: List[Dict]) -> Dict:
        """Calculate how often user journals."""
        if len(entries) < 2:
            return {'avg_entries_per_day': 0}

        # Get date range
        dates = []
        for entry in entries:
            ts = parse_iso_timestamp(entry.get('timestamp'))
            if ts:
                dates.append(ts.date())
        if not dates:
            return {'avg_entries_per_day': 0, 'total_days': 0}
        date_range = (max(dates) - min(dates)).days + 1

        avg_per_day = len(entries) / date_range

        return {
            'avg_entries_per_day': round(avg_per_day, 2),
            'total_days': date_range
        }

    def _calculate_keyword_baseline(self, entries: List[Dict]) -> Dict:
        """Calculate common themes/keywords."""
        all_keywords = []

        for entry in entries:
            keywords_json = entry.get('keywords_json')
            if keywords_json:
                try:
                    keywords = json.loads(keywords_json) if isinstance(keywords_json, str) else keywords_json
                    all_keywords.extend(keywords)
                except:
                    pass

        if not all_keywords:
            return {'top_themes': []}

        keyword_counts = Counter(all_keywords)
        top_themes = [kw for kw, count in keyword_counts.most_common(10)]

        return {
            'top_themes': top_themes
        }

    def _get_date_range(self, entries: List[Dict]) -> Tuple[str, str]:
        """Get start and end dates of entries."""
        dates = []
        for entry in entries:
            ts = parse_iso_timestamp(entry.get('timestamp'))
            if ts:
                dates.append(ts)
        if not dates:
            return ("", "")
        return (min(dates).isoformat(), max(dates).isoformat())

    def _compare_sentiment(self, analysis: Dict, baseline: Dict) -> Optional[Dict]:
        """Compare current sentiment to baseline."""
        current = analysis.get('text_analysis', {}).get('sentiment_compound', 0)
        base_mean = baseline['sentiment']['mean']
        base_std = baseline['sentiment']['std']

        # Calculate z-score (how many standard deviations from mean)
        if base_std > 0:
            z_score = abs(current - base_mean) / base_std
        else:
            z_score = abs(current - base_mean) / 0.3  # Default std if zero

        # Significant if > 2 standard deviations
        if z_score > 2:
            direction = "more positive" if current > base_mean else "more negative"
            return {
                'dimension': 'sentiment',
                'score': min(1.0, z_score / 4),  # Normalize to 0-1
                'description': f"Sentiment significantly {direction} than baseline ({current:.2f} vs {base_mean:.2f})",
                'current': current,
                'baseline': base_mean
            }

        return None

    def _compare_emotion(self, analysis: Dict, baseline: Dict) -> Optional[Dict]:
        """Compare current emotion to baseline distribution."""
        current_emotion = analysis.get('primary_emotion', 'neutral')
        distribution = baseline['emotions']['distribution']

        # Check if this emotion is rare for this user
        current_freq = distribution.get(current_emotion, 0)

        # Unusual if less than 10% of their typical emotions
        if current_freq < 0.10:
            return {
                'dimension': 'emotion',
                'score': 1.0 - current_freq,  # Lower frequency = higher deviation
                'description': f"Unusual emotion: {current_emotion} (only {current_freq:.0%} of baseline)",
                'current': current_emotion,
                'baseline_frequency': current_freq
            }

        return None

    def _compare_intensity(self, analysis: Dict, baseline: Dict) -> Optional[Dict]:
        """Compare current intensity to baseline."""
        current = analysis.get('intensity', {}).get('intensity', 0.5)
        base_mean = baseline['intensity']['mean']
        base_std = baseline['intensity']['std']

        # Calculate z-score
        if base_std > 0:
            z_score = abs(current - base_mean) / base_std
        else:
            z_score = abs(current - base_mean) / 0.2

        # Significant if > 2 standard deviations
        if z_score > 2:
            direction = "stronger" if current > base_mean else "weaker"
            return {
                'dimension': 'intensity',
                'score': min(1.0, z_score / 4),
                'description': f"Intensity {direction} than typical ({current:.2f} vs {base_mean:.2f})",
                'current': current,
                'baseline': base_mean
            }

        return None

    def _compare_prosody(self, analysis: Dict, baseline: Dict) -> Optional[Dict]:
        """Compare voice prosody to baseline."""
        if not baseline.get('prosody'):
            return None

        current_tone = analysis.get('voice_analysis', {}).get('prosody_emotion')
        if not current_tone:
            return None

        distribution = baseline['prosody']['distribution']
        current_freq = distribution.get(current_tone, 0)

        # Unusual if less than 10% of typical voice tones
        if current_freq < 0.10:
            return {
                'dimension': 'prosody',
                'score': 1.0 - current_freq,
                'description': f"Unusual voice tone: {current_tone} (only {current_freq:.0%} of baseline)",
                'current': current_tone,
                'baseline_frequency': current_freq
            }

        return None

    def _generate_interpretation(self, deviations: List[Dict], severity: float) -> str:
        """Generate human-readable interpretation."""
        if not deviations:
            return "Current state matches your typical emotional baseline"

        if severity >= 0.7:
            level = "Significant deviation"
        elif severity >= 0.5:
            level = "Moderate deviation"
        else:
            level = "Minor deviation"

        details = [d['description'] for d in deviations[:3]]  # Top 3

        return f"{level} from baseline. {'; '.join(details)}"

    def _empty_baseline(self, user_id: Optional[str]) -> Dict:
        """Return empty baseline structure."""
        return {
            'sentiment': {'mean': 0, 'std': 0, 'range': (0, 0)},
            'emotions': {'distribution': {}, 'most_common': None},
            'prosody': None,
            'intensity': {'mean': 0.5, 'std': 0.2, 'range': (0, 1)},
            'time_patterns': {},
            'entry_frequency': {'avg_entries_per_day': 0},
            'keywords': {'top_themes': []},
            'metadata': {
                'user_id': user_id,
                'entry_count': 0,
                'baseline_created': datetime.now().isoformat(),
                'sufficient_data': False,
                'reason': 'No entries provided'
            }
        }

    def _insufficient_data_baseline(self, user_id: Optional[str], count: int) -> Dict:
        """Return baseline indicating insufficient data."""
        return {
            'sentiment': {'mean': 0, 'std': 0, 'range': (0, 0)},
            'emotions': {'distribution': {}, 'most_common': None},
            'prosody': None,
            'intensity': {'mean': 0.5, 'std': 0.2, 'range': (0, 1)},
            'time_patterns': {},
            'entry_frequency': {'avg_entries_per_day': 0},
            'keywords': {'top_themes': []},
            'metadata': {
                'user_id': user_id,
                'entry_count': count,
                'baseline_created': datetime.now().isoformat(),
                'sufficient_data': False,
                'reason': f'Insufficient data: {count} entries (need {self.min_entries}+)'
            }
        }

    def _insufficient_baseline(self) -> Dict:
        """Return deviation result when baseline is insufficient."""
        return {
            'is_deviation': False,
            'severity': 0.0,
            'dimensions': [],
            'interpretation': 'Cannot compare - insufficient baseline data',
            'timestamp': datetime.now().isoformat()
        }
