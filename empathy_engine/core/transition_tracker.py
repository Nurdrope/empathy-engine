"""
EmpathyEngine - Emotion Transition Tracker
Tracks how emotions change over time and identifies transition patterns

This module analyzes emotional flows:
- What emotion typically follows what (joy → calm, anger → sadness, etc.)
- Transition speed (rapid vs gradual shifts)
- Cyclical patterns (recurring emotion sequences)
- Trigger-response patterns (event → emotion change)
- Regulatory patterns (coping strategies that shift emotions)

Example insights:
- "You often go from anxiety → journaling → calm"
- "Anger typically shifts to sadness within 2 hours"
- "You have a weekly cycle: Sunday anxiety → Monday motivation"

Created: December 18, 2025
Part of the "all of them" expansion
"""

from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple
from collections import Counter, defaultdict
import numpy as np
from ..utils.time import parse_iso_timestamp


class TransitionTracker:
    """
    Tracks emotional transitions and identifies patterns.

    Transition types:
    - Sequential: Direct A → B transitions
    - Cyclical: Recurring sequences (A → B → C → A)
    - Triggered: Event-driven transitions
    - Regulatory: Coping-driven transitions
    - Rapid: Quick shifts (<1 hour)
    - Gradual: Slow shifts (hours/days)

    Usage:
        tracker = TransitionTracker()

        # Analyze transitions from historical data
        patterns = tracker.analyze_transitions(entries)

        # Track current transition
        transition = tracker.track_transition(prev_analysis, current_analysis)
    """

    def __init__(self):
        # Emotion valence (for detecting emotional direction)
        self.emotion_valence = {
            'joy': 1.0,
            'surprise': 0.5,
            'neutral': 0.0,
            'anxiety': -0.3,
            'fear': -0.6,
            'sadness': -0.7,
            'anger': -0.8,
            'disgust': -0.9,
            # Additional emotions
            'calm': 0.3,
            'excited': 0.8,
            'frustrated': -0.5,
            'content': 0.6,
            'stressed': -0.4
        }

    def analyze_transitions(
        self,
        entries: List[Dict],
        min_transition_count: int = 3
    ) -> Dict:
        """
        Analyze emotional transitions from historical entries.

        Args:
            entries: List of historical entry dicts (must be sorted by timestamp)
            min_transition_count: Minimum occurrences to consider a pattern

        Returns:
            Dict with:
            - transition_matrix: Emotion A → Emotion B frequencies
            - common_transitions: Most frequent transitions
            - transition_speeds: How fast emotions typically change
            - cyclical_patterns: Recurring emotion sequences
            - regulatory_transitions: Transitions after coping activities
            - emotional_momentum: Tendency to stay in or shift from emotions
        """
        if len(entries) < 2:
            return self._empty_analysis()

        valid_entries = []
        for entry in entries:
            if parse_iso_timestamp(entry.get('timestamp')):
                valid_entries.append(entry)
        if len(valid_entries) < 2:
            return self._empty_analysis()

        # Sort by timestamp
        sorted_entries = sorted(
            valid_entries,
            key=lambda e: parse_iso_timestamp(e.get('timestamp'))
        )

        # Build transition matrix
        transition_counts = defaultdict(Counter)
        transition_times = defaultdict(list)
        all_transitions = []

        for i in range(len(sorted_entries) - 1):
            current = sorted_entries[i]
            next_entry = sorted_entries[i + 1]

            current_emotion = current.get('emotion_primary')
            next_emotion = next_entry.get('emotion_primary')

            if current_emotion and next_emotion:
                # Record transition
                transition_counts[current_emotion][next_emotion] += 1

                # Record transition time
                time_diff = self._time_difference(current['timestamp'], next_entry['timestamp'])
                transition_times[(current_emotion, next_emotion)].append(time_diff)

                # Record for sequence analysis
                all_transitions.append({
                    'from': current_emotion,
                    'to': next_emotion,
                    'time_diff': time_diff,
                    'from_sentiment': current.get('sentiment_compound', 0),
                    'to_sentiment': next_entry.get('sentiment_compound', 0)
                })

        # Find common transitions
        common_transitions = self._find_common_transitions(
            transition_counts,
            min_transition_count
        )

        # Analyze transition speeds
        transition_speeds = self._analyze_speeds(transition_times)

        # Find cyclical patterns
        cyclical_patterns = self._find_cycles(sorted_entries)

        # Detect regulatory transitions (coping-driven)
        regulatory = self._detect_regulatory_transitions(sorted_entries)

        # Calculate emotional momentum
        momentum = self._calculate_momentum(transition_counts)

        # Identify dominant flows
        dominant_flows = self._identify_flows(all_transitions)

        return {
            'transition_matrix': dict(transition_counts),
            'common_transitions': common_transitions,
            'transition_speeds': transition_speeds,
            'cyclical_patterns': cyclical_patterns,
            'regulatory_transitions': regulatory,
            'emotional_momentum': momentum,
            'dominant_flows': dominant_flows,
            'total_transitions': len(all_transitions)
        }

    def track_transition(
        self,
        previous: Dict,
        current: Dict,
        transition_patterns: Optional[Dict] = None
    ) -> Dict:
        """
        Track a specific transition between two emotional states.

        Args:
            previous: Previous analysis result
            current: Current analysis result
            transition_patterns: Optional patterns from analyze_transitions()

        Returns:
            Dict with:
            - transition: (from_emotion, to_emotion)
            - direction: 'positive', 'negative', or 'neutral'
            - speed: 'rapid' or 'gradual'
            - time_elapsed: Hours between states
            - is_common: Whether this transition is typical for this user
            - interpretation: Human-readable description
        """
        from_emotion = previous.get('primary_emotion', 'neutral')
        to_emotion = current.get('primary_emotion', 'neutral')

        from_timestamp = previous.get('text_analysis', {}).get('timestamp') or datetime.now().isoformat()
        to_timestamp = current.get('text_analysis', {}).get('timestamp') or datetime.now().isoformat()

        time_elapsed = self._time_difference(from_timestamp, to_timestamp)

        # Determine direction
        direction = self._get_transition_direction(from_emotion, to_emotion, previous, current)

        # Determine speed
        speed = 'rapid' if time_elapsed < 1.0 else 'gradual'

        # Check if common transition (if patterns provided)
        is_common = False
        if transition_patterns and 'common_transitions' in transition_patterns:
            common_pairs = [(t['from'], t['to']) for t in transition_patterns['common_transitions']]
            is_common = (from_emotion, to_emotion) in common_pairs

        # Generate interpretation
        interpretation = self._interpret_transition(
            from_emotion,
            to_emotion,
            direction,
            speed,
            time_elapsed,
            is_common
        )

        return {
            'transition': (from_emotion, to_emotion),
            'direction': direction,
            'speed': speed,
            'time_elapsed_hours': round(time_elapsed, 2),
            'is_common': is_common,
            'interpretation': interpretation
        }

    def _time_difference(self, timestamp1: str, timestamp2: str) -> float:
        """Calculate time difference in hours."""
        dt1 = parse_iso_timestamp(timestamp1)
        dt2 = parse_iso_timestamp(timestamp2)
        if not dt1 or not dt2:
            return 0.0
        return abs((dt2 - dt1).total_seconds() / 3600)

    def _find_common_transitions(
        self,
        transition_counts: Dict,
        min_count: int
    ) -> List[Dict]:
        """Find most common emotion transitions."""
        common = []

        for from_emotion, to_emotions in transition_counts.items():
            for to_emotion, count in to_emotions.items():
                if count >= min_count:
                    common.append({
                        'from': from_emotion,
                        'to': to_emotion,
                        'count': count,
                        'description': f"{from_emotion} → {to_emotion} ({count} times)"
                    })

        # Sort by count
        common.sort(key=lambda x: x['count'], reverse=True)
        return common

    def _analyze_speeds(self, transition_times: Dict) -> Dict:
        """Analyze typical transition speeds."""
        speeds = {}

        for (from_emotion, to_emotion), times in transition_times.items():
            avg_time = np.mean(times)
            speed_category = 'rapid' if avg_time < 1.0 else 'gradual'

            speeds[f"{from_emotion}→{to_emotion}"] = {
                'avg_hours': round(avg_time, 2),
                'min_hours': round(min(times), 2),
                'max_hours': round(max(times), 2),
                'category': speed_category
            }

        return speeds

    def _find_cycles(self, entries: List[Dict]) -> List[Dict]:
        """
        Find cyclical emotion patterns.

        Example: anxiety → calm → joy → anxiety (repeating)
        """
        if len(entries) < 4:
            return []

        # Extract emotion sequence
        emotions = [e.get('emotion_primary') for e in entries if e.get('emotion_primary')]

        cycles = []

        # Look for repeating sequences of length 3-5
        for cycle_length in range(3, 6):
            for i in range(len(emotions) - cycle_length * 2):
                sequence = tuple(emotions[i:i+cycle_length])
                next_sequence = tuple(emotions[i+cycle_length:i+cycle_length*2])

                # If same sequence appears twice in a row, it's a cycle
                if sequence == next_sequence:
                    cycles.append({
                        'sequence': list(sequence),
                        'length': cycle_length,
                        'description': ' → '.join(sequence) + ' → (repeat)'
                    })

        # Remove duplicates
        unique_cycles = []
        seen = set()
        for cycle in cycles:
            seq_str = str(cycle['sequence'])
            if seq_str not in seen:
                seen.add(seq_str)
                unique_cycles.append(cycle)

        return unique_cycles

    def _detect_regulatory_transitions(self, entries: List[Dict]) -> List[Dict]:
        """
        Detect transitions that follow coping activities.

        Looks for:
        - Negative emotion → (coping keywords) → positive shift
        """
        coping_keywords = [
            'breathe', 'breathing', 'meditate', 'meditation', 'journal',
            'walk', 'exercise', 'talk', 'friend', 'therapist', 'music',
            'rest', 'sleep', 'shower', 'bath', 'break'
        ]

        regulatory = []

        for i in range(len(entries) - 1):
            current = entries[i]
            next_entry = entries[i + 1]

            current_emotion = current.get('emotion_primary')
            next_emotion = next_entry.get('emotion_primary')
            current_text = current.get('text', '').lower()

            # Check if coping activity mentioned
            coping_mentioned = any(kw in current_text for kw in coping_keywords)

            if coping_mentioned:
                # Check if emotion improved
                current_val = self.emotion_valence.get(current_emotion, 0)
                next_val = self.emotion_valence.get(next_emotion, 0)

                if next_val > current_val:
                    # Extract which coping strategy
                    strategies = [kw for kw in coping_keywords if kw in current_text]

                    regulatory.append({
                        'from': current_emotion,
                        'to': next_emotion,
                        'strategy': strategies[0] if strategies else 'coping',
                        'description': f"{current_emotion} → {strategies[0] if strategies else 'coping'} → {next_emotion}"
                    })

        return regulatory

    def _calculate_momentum(self, transition_counts: Dict) -> Dict:
        """
        Calculate emotional momentum - tendency to stay vs shift.

        High momentum = emotions tend to persist
        Low momentum = emotions change frequently
        """
        total_transitions = 0
        same_emotion_count = 0

        for from_emotion, to_emotions in transition_counts.items():
            for to_emotion, count in to_emotions.items():
                total_transitions += count
                if from_emotion == to_emotion:
                    same_emotion_count += count

        if total_transitions == 0:
            return {'persistence_rate': 0, 'change_rate': 0}

        persistence_rate = same_emotion_count / total_transitions
        change_rate = 1 - persistence_rate

        return {
            'persistence_rate': round(persistence_rate, 3),
            'change_rate': round(change_rate, 3),
            'interpretation': 'high' if persistence_rate > 0.5 else 'low'
        }

    def _identify_flows(self, transitions: List[Dict]) -> Dict:
        """
        Identify dominant emotional flows.

        Upward flow: Negative → Positive
        Downward flow: Positive → Negative
        Stable: Emotions stay similar
        """
        upward = 0
        downward = 0
        stable = 0

        for t in transitions:
            from_sent = t['from_sentiment']
            to_sent = t['to_sentiment']

            diff = to_sent - from_sent

            if diff > 0.2:
                upward += 1
            elif diff < -0.2:
                downward += 1
            else:
                stable += 1

        total = len(transitions)
        if total == 0:
            return {}

        return {
            'upward_flow': round(upward / total, 3),
            'downward_flow': round(downward / total, 3),
            'stable_flow': round(stable / total, 3),
            'dominant_direction': max(
                [('upward', upward), ('downward', downward), ('stable', stable)],
                key=lambda x: x[1]
            )[0]
        }

    def _get_transition_direction(
        self,
        from_emotion: str,
        to_emotion: str,
        from_analysis: Dict,
        to_analysis: Dict
    ) -> str:
        """Determine if transition is positive, negative, or neutral."""
        # Use sentiment as primary indicator
        from_sent = from_analysis.get('text_analysis', {}).get('sentiment_compound', 0)
        to_sent = to_analysis.get('text_analysis', {}).get('sentiment_compound', 0)

        diff = to_sent - from_sent

        if diff > 0.2:
            return 'positive'
        elif diff < -0.2:
            return 'negative'
        else:
            return 'neutral'

    def _interpret_transition(
        self,
        from_emotion: str,
        to_emotion: str,
        direction: str,
        speed: str,
        time_elapsed: float,
        is_common: bool
    ) -> str:
        """Generate human-readable interpretation."""
        if from_emotion == to_emotion:
            return f"Emotional state persisted: {from_emotion}"

        parts = []

        # Direction
        if direction == 'positive':
            parts.append("✓ Positive shift")
        elif direction == 'negative':
            parts.append("⚠ Negative shift")
        else:
            parts.append("→ Neutral shift")

        # Transition
        parts.append(f"{from_emotion} → {to_emotion}")

        # Speed
        if speed == 'rapid':
            parts.append(f"(rapid, {time_elapsed:.1f}h)")
        else:
            parts.append(f"(gradual, {time_elapsed:.1f}h)")

        # Common pattern
        if is_common:
            parts.append("[typical pattern for you]")

        return " ".join(parts)

    def _empty_analysis(self) -> Dict:
        """Return empty analysis structure."""
        return {
            'transition_matrix': {},
            'common_transitions': [],
            'transition_speeds': {},
            'cyclical_patterns': [],
            'regulatory_transitions': [],
            'emotional_momentum': {'persistence_rate': 0, 'change_rate': 0},
            'dominant_flows': {},
            'total_transitions': 0
        }
