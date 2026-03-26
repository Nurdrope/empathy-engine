"""
EmpathyEngine - Emotion Prediction Engine
Predicts likely emotional states based on patterns, context, and triggers

This module forecasts emotions using:
- Transition patterns (what typically follows current emotion)
- Time patterns (recurring weekly/daily emotional rhythms)
- Trigger patterns (events that predictably cause emotions)
- Seasonal/cyclical patterns
- Baseline deviations (return to baseline predictions)

Example predictions:
- "Based on your pattern, anxiety on Sunday evenings is likely"
- "After work stress, you typically shift to calm within 2 hours"
- "Low energy detected - sadness likely to follow"

Created: December 18, 2025
Part of the "all of them" expansion
"""

from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple
from collections import Counter, defaultdict
import numpy as np
from ..utils.time import parse_iso_timestamp


class EmotionPredictor:
    """
    Predicts future emotional states based on historical patterns.

    Prediction methods:
    1. Transition-based: What emotion typically follows current state
    2. Time-based: Recurring patterns at specific times/days
    3. Trigger-based: Event → emotion predictions
    4. Baseline regression: Tendency to return to baseline
    5. Cyclical: Seasonal and weekly cycles

    Confidence levels:
    - 0.8-1.0: High confidence (strong historical pattern)
    - 0.5-0.8: Moderate confidence (some pattern evidence)
    - 0.0-0.5: Low confidence (limited data or weak pattern)

    Usage:
        predictor = EmotionPredictor()

        # Learn patterns from historical data
        predictor.learn_patterns(historical_entries)

        # Predict next emotion
        prediction = predictor.predict_next(current_analysis)
        # Returns: {'emotion': 'calm', 'confidence': 0.75, 'timeframe': '1-3 hours'}
    """

    def __init__(self):
        self.transition_patterns = {}
        self.time_patterns = {}
        self.trigger_patterns = {}
        self.baseline = None
        self.cyclical_patterns = {}

    def learn_patterns(
        self,
        entries: List[Dict],
        baseline: Optional[Dict] = None
    ) -> Dict:
        """
        Learn predictive patterns from historical data.

        Args:
            entries: List of historical entry dicts
            baseline: Optional baseline profile

        Returns:
            Dict with learned patterns
        """
        if len(entries) < 10:
            return {'status': 'insufficient_data', 'entry_count': len(entries)}

        # Sort by timestamp
        sorted_entries = sorted(entries, key=lambda e: e['timestamp'])

        # Learn transition patterns
        self.transition_patterns = self._learn_transitions(sorted_entries)

        # Learn time patterns
        self.time_patterns = self._learn_time_patterns(sorted_entries)

        # Learn trigger patterns
        self.trigger_patterns = self._learn_triggers(sorted_entries)

        # Learn cyclical patterns
        self.cyclical_patterns = self._learn_cycles(sorted_entries)

        # Store baseline
        self.baseline = baseline

        return {
            'status': 'patterns_learned',
            'transition_patterns': len(self.transition_patterns),
            'time_patterns': len(self.time_patterns),
            'trigger_patterns': len(self.trigger_patterns),
            'cyclical_patterns': len(self.cyclical_patterns)
        }

    def predict_next(
        self,
        current_analysis: Dict,
        timeframe: str = 'short'  # 'short' (1-3h), 'medium' (3-24h), 'long' (1-7d)
    ) -> Dict:
        """
        Predict next likely emotional state.

        Args:
            current_analysis: Current analysis result
            timeframe: Prediction timeframe

        Returns:
            Dict with:
            - emotion: Predicted emotion
            - confidence: Prediction confidence 0-1
            - timeframe: Expected time to transition
            - method: Which prediction method was used
            - alternatives: Other possible emotions
        """
        current_emotion = current_analysis.get('primary_emotion', 'neutral')
        current_time = parse_iso_timestamp(
            current_analysis.get('text_analysis', {}).get('timestamp')
        ) or datetime.now()

        predictions = []

        # Method 1: Transition-based prediction
        if current_emotion in self.transition_patterns:
            trans_pred = self._predict_from_transitions(current_emotion)
            if trans_pred:
                predictions.append(trans_pred)

        # Method 2: Time-based prediction
        time_pred = self._predict_from_time(current_time, timeframe)
        if time_pred:
            predictions.append(time_pred)

        # Method 3: Baseline regression (tendency to return to baseline)
        if self.baseline:
            baseline_pred = self._predict_baseline_return(current_emotion, current_analysis)
            if baseline_pred:
                predictions.append(baseline_pred)

        # Method 4: Cyclical patterns
        cycle_pred = self._predict_from_cycles(current_time, timeframe)
        if cycle_pred:
            predictions.append(cycle_pred)

        # Combine predictions (weighted by confidence)
        if not predictions:
            return self._no_prediction()

        # Select highest confidence prediction
        best_prediction = max(predictions, key=lambda p: p['confidence'])

        # Get alternatives (other high-confidence predictions)
        alternatives = [
            {'emotion': p['emotion'], 'confidence': p['confidence']}
            for p in predictions
            if p['emotion'] != best_prediction['emotion'] and p['confidence'] > 0.5
        ]

        return {
            'emotion': best_prediction['emotion'],
            'confidence': round(best_prediction['confidence'], 3),
            'timeframe': best_prediction['timeframe'],
            'method': best_prediction['method'],
            'alternatives': alternatives,
            'interpretation': self._generate_interpretation(best_prediction, current_emotion)
        }

    def predict_for_time(
        self,
        target_time: datetime,
        current_emotion: Optional[str] = None
    ) -> Dict:
        """
        Predict emotional state at a specific future time.

        Args:
            target_time: When to predict for
            current_emotion: Optional current emotion

        Returns:
            Prediction dict
        """
        # Use time patterns and cyclical patterns
        predictions = []

        # Time-based prediction
        time_pred = self._predict_from_time(target_time, 'custom')
        if time_pred:
            predictions.append(time_pred)

        # Cyclical prediction
        cycle_pred = self._predict_from_cycles(target_time, 'custom')
        if cycle_pred:
            predictions.append(cycle_pred)

        if not predictions:
            return self._no_prediction()

        best = max(predictions, key=lambda p: p['confidence'])

        return {
            'emotion': best['emotion'],
            'confidence': round(best['confidence'], 3),
            'target_time': target_time.isoformat(),
            'method': best['method']
        }

    def _learn_transitions(self, entries: List[Dict]) -> Dict:
        """Learn emotion A → emotion B transition patterns."""
        transitions = defaultdict(Counter)

        for i in range(len(entries) - 1):
            current = entries[i].get('emotion_primary')
            next_emotion = entries[i + 1].get('emotion_primary')

            if current and next_emotion:
                transitions[current][next_emotion] += 1

        # Convert to probabilities
        patterns = {}
        for from_emotion, to_emotions in transitions.items():
            total = sum(to_emotions.values())
            patterns[from_emotion] = {
                emotion: count / total
                for emotion, count in to_emotions.items()
            }

        return patterns

    def _learn_time_patterns(self, entries: List[Dict]) -> Dict:
        """Learn time-based emotion patterns."""
        # Track emotions by hour and day of week
        hour_emotions = defaultdict(Counter)
        day_emotions = defaultdict(Counter)

        for entry in entries:
            dt = parse_iso_timestamp(entry.get('timestamp'))
            if not dt:
                continue
            emotion = entry.get('emotion_primary')

            if emotion:
                hour_emotions[dt.hour][emotion] += 1
                day_emotions[dt.weekday()][emotion] += 1

        # Convert to patterns
        patterns = {
            'hourly': {},
            'daily': {}
        }

        # Hourly patterns
        for hour, emotions in hour_emotions.items():
            total = sum(emotions.values())
            if total >= 3:  # Need at least 3 occurrences
                patterns['hourly'][hour] = {
                    emotion: count / total
                    for emotion, count in emotions.most_common(3)
                }

        # Daily patterns
        for day, emotions in day_emotions.items():
            total = sum(emotions.values())
            if total >= 2:
                patterns['daily'][day] = {
                    emotion: count / total
                    for emotion, count in emotions.most_common(3)
                }

        return patterns

    def _learn_triggers(self, entries: List[Dict]) -> Dict:
        """Learn event → emotion trigger patterns."""
        # Simple keyword-based trigger detection
        trigger_keywords = {
            'work': ['work', 'job', 'boss', 'meeting'],
            'social': ['friend', 'party', 'date'],
            'health': ['doctor', 'sick', 'pain'],
            'family': ['mom', 'dad', 'family']
        }

        triggers = defaultdict(Counter)

        for entry in entries:
            text = entry.get('text', '').lower()
            emotion = entry.get('emotion_primary')

            if emotion:
                for category, keywords in trigger_keywords.items():
                    if any(kw in text for kw in keywords):
                        triggers[category][emotion] += 1

        # Convert to probabilities
        patterns = {}
        for trigger, emotions in triggers.items():
            total = sum(emotions.values())
            if total >= 3:
                patterns[trigger] = {
                    emotion: count / total
                    for emotion, count in emotions.items()
                }

        return patterns

    def _learn_cycles(self, entries: List[Dict]) -> Dict:
        """Learn cyclical patterns (weekly, monthly)."""
        # Track sentiment trends by day of week
        weekday_sentiments = defaultdict(list)

        for entry in entries:
            dt = parse_iso_timestamp(entry.get('timestamp'))
            if not dt:
                continue
            sentiment = entry.get('sentiment_compound', 0)
            weekday_sentiments[dt.weekday()].append(sentiment)

        # Calculate average sentiment per weekday
        patterns = {}
        for day, sentiments in weekday_sentiments.items():
            if len(sentiments) >= 3:
                avg_sentiment = np.mean(sentiments)
                # Predict emotion from sentiment
                if avg_sentiment > 0.3:
                    predicted_emotion = 'joy'
                elif avg_sentiment < -0.3:
                    predicted_emotion = 'sadness'
                else:
                    predicted_emotion = 'neutral'

                patterns[day] = {
                    'avg_sentiment': round(avg_sentiment, 2),
                    'predicted_emotion': predicted_emotion,
                    'confidence': min(len(sentiments) / 10, 0.9)  # More data = higher confidence
                }

        return patterns

    def _predict_from_transitions(self, current_emotion: str) -> Optional[Dict]:
        """Predict based on transition patterns."""
        if current_emotion not in self.transition_patterns:
            return None

        probabilities = self.transition_patterns[current_emotion]

        # Most likely next emotion
        next_emotion = max(probabilities, key=probabilities.get)
        confidence = probabilities[next_emotion]

        # Skip if same emotion (not a real transition)
        if next_emotion == current_emotion:
            # Get second most likely
            sorted_probs = sorted(probabilities.items(), key=lambda x: x[1], reverse=True)
            if len(sorted_probs) > 1:
                next_emotion = sorted_probs[1][0]
                confidence = sorted_probs[1][1]
            else:
                return None

        return {
            'emotion': next_emotion,
            'confidence': confidence,
            'timeframe': '1-3 hours',
            'method': 'transition_pattern'
        }

    def _predict_from_time(self, target_time: datetime, timeframe: str) -> Optional[Dict]:
        """Predict based on time patterns."""
        # Check hourly pattern
        if target_time.hour in self.time_patterns.get('hourly', {}):
            hour_pattern = self.time_patterns['hourly'][target_time.hour]
            emotion = max(hour_pattern, key=hour_pattern.get)
            confidence = hour_pattern[emotion]

            return {
                'emotion': emotion,
                'confidence': confidence,
                'timeframe': f'at {target_time.hour}:00',
                'method': 'time_pattern'
            }

        # Check daily pattern
        if target_time.weekday() in self.time_patterns.get('daily', {}):
            day_pattern = self.time_patterns['daily'][target_time.weekday()]
            emotion = max(day_pattern, key=day_pattern.get)
            confidence = day_pattern[emotion]

            days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

            return {
                'emotion': emotion,
                'confidence': confidence,
                'timeframe': f'on {days[target_time.weekday()]}s',
                'method': 'time_pattern'
            }

        return None

    def _predict_baseline_return(
        self,
        current_emotion: str,
        current_analysis: Dict
    ) -> Optional[Dict]:
        """Predict return to baseline emotion."""
        if not self.baseline:
            return None

        baseline_emotion = self.baseline.get('emotions', {}).get('most_common')
        if not baseline_emotion:
            return None

        # If currently away from baseline, predict return
        if current_emotion != baseline_emotion:
            # Confidence based on how strong baseline is
            baseline_freq = self.baseline['emotions']['distribution'].get(baseline_emotion, 0)

            return {
                'emotion': baseline_emotion,
                'confidence': baseline_freq * 0.7,  # Moderate confidence
                'timeframe': '3-24 hours',
                'method': 'baseline_regression'
            }

        return None

    def _predict_from_cycles(self, target_time: datetime, timeframe: str) -> Optional[Dict]:
        """Predict based on cyclical patterns."""
        weekday = target_time.weekday()

        if weekday in self.cyclical_patterns:
            pattern = self.cyclical_patterns[weekday]

            return {
                'emotion': pattern['predicted_emotion'],
                'confidence': pattern['confidence'],
                'timeframe': 'cyclical (weekly pattern)',
                'method': 'cyclical_pattern'
            }

        return None

    def _generate_interpretation(self, prediction: Dict, current_emotion: str) -> str:
        """Generate human-readable interpretation."""
        emotion = prediction['emotion']
        confidence = prediction['confidence']
        method = prediction['method']
        timeframe = prediction['timeframe']

        if current_emotion == emotion:
            return f"Likely to remain {emotion} ({confidence:.0%} confidence) - {method}"

        method_names = {
            'transition_pattern': 'based on your typical emotional transitions',
            'time_pattern': 'based on recurring time patterns',
            'baseline_regression': 'tendency to return to your baseline',
            'cyclical_pattern': 'based on weekly emotional cycles'
        }

        method_desc = method_names.get(method, method)

        return f"Predicted: {current_emotion} → {emotion} ({confidence:.0%} confidence) in {timeframe}, {method_desc}"

    def _no_prediction(self) -> Dict:
        """Return structure when no prediction available."""
        return {
            'emotion': None,
            'confidence': 0.0,
            'timeframe': None,
            'method': None,
            'alternatives': [],
            'interpretation': 'Insufficient data for prediction'
        }
