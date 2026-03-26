"""
EmpathyEngine - Emotional Trigger Identifier
Identifies specific events, situations, or stimuli that trigger emotional responses

This module discovers:
- What causes emotional shifts (work stress, social events, etc.)
- Positive triggers (what makes you happy/calm)
- Negative triggers (what causes anxiety/sadness)
- Temporal triggers (time-based patterns)
- Compound triggers (multiple factors combining)

Example insights:
- "Monday mornings trigger anxiety (8/10 occurrences)"
- "Talking to friends consistently shifts you from sad to happy"
- "Mentions of 'deadline' correlate with stress 85% of the time"

Created: December 18, 2025
Part of the "all of them" expansion
"""

import re
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple
from collections import Counter, defaultdict
from ..utils.time import parse_iso_timestamp


class TriggerIdentifier:
    """
    Identifies emotional triggers from historical patterns.

    Trigger types:
    - Event triggers: Specific events → emotions
    - Keyword triggers: Certain words → emotions
    - Temporal triggers: Times/days → emotions
    - Social triggers: People/interactions → emotions
    - Activity triggers: Actions → emotions
    - Compound triggers: Multiple factors → emotions

    Usage:
        identifier = TriggerIdentifier()

        # Learn triggers from history
        triggers = identifier.identify_triggers(entries)

        # Check if current situation matches known trigger
        match = identifier.check_for_trigger(current_analysis, triggers)
    """

    def __init__(self):
        # Event categories to track
        self.event_keywords = {
            'work_stress': [
                r'\b(deadline|meeting|boss|presentation|report|project|urgent)\b'
            ],
            'work_positive': [
                r'\b(promotion|raise|accomplished|finished|completed|success at work)\b'
            ],
            'social_positive': [
                r'\b(friend|friends|hanging out|party|date|fun|laugh)\b'
            ],
            'social_negative': [
                r'\b(argument|fight|lonely|alone|rejected|ignored|cancel)\b'
            ],
            'family_stress': [
                r'\b(family drama|parents fighting|family issues|mom dad)\b'
            ],
            'health_concern': [
                r'\b(doctor|pain|sick|symptom|worried about health)\b'
            ],
            'financial_stress': [
                r'\b(money|bills|debt|broke|expensive|can\'t afford)\b'
            ],
            'achievement': [
                r'\b(won|passed|accomplished|proud|achieved|goal)\b'
            ],
            'exercise': [
                r'\b(workout|gym|run|exercise|yoga)\b'
            ],
            'nature': [
                r'\b(walk|outside|nature|park|sunshine|fresh air)\b'
            ],
            'rest': [
                r'\b(nap|sleep|rest|relax|break)\b'
            ]
        }

        # People keywords
        self.people_keywords = [
            'mom', 'dad', 'mother', 'father', 'parent',
            'friend', 'boyfriend', 'girlfriend', 'partner',
            'boss', 'coworker', 'colleague',
            'therapist', 'doctor'
        ]

    def identify_triggers(
        self,
        entries: List[Dict],
        min_occurrences: int = 3
    ) -> Dict:
        """
        Identify emotional triggers from historical entries.

        Args:
            entries: List of historical entry dicts
            min_occurrences: Minimum times trigger must occur

        Returns:
            Dict with:
            - event_triggers: Event → emotion correlations
            - keyword_triggers: Keywords → emotion correlations
            - temporal_triggers: Time patterns → emotions
            - social_triggers: People → emotion correlations
            - positive_triggers: What causes positive shifts
            - negative_triggers: What causes negative shifts
        """
        if len(entries) < 10:
            return {'status': 'insufficient_data'}

        # Sort by timestamp
        sorted_entries = sorted(entries, key=lambda e: e['timestamp'])

        triggers = {
            'event_triggers': self._identify_event_triggers(sorted_entries, min_occurrences),
            'keyword_triggers': self._identify_keyword_triggers(sorted_entries, min_occurrences),
            'temporal_triggers': self._identify_temporal_triggers(sorted_entries, min_occurrences),
            'social_triggers': self._identify_social_triggers(sorted_entries, min_occurrences),
            'transition_triggers': self._identify_transition_triggers(sorted_entries, min_occurrences),
            'positive_triggers': [],
            'negative_triggers': []
        }

        # Separate positive and negative triggers
        all_triggers = []
        for category, category_triggers in triggers.items():
            if category not in ['positive_triggers', 'negative_triggers']:
                all_triggers.extend(category_triggers)

        for trigger in all_triggers:
            if trigger.get('effect') == 'positive':
                triggers['positive_triggers'].append(trigger)
            elif trigger.get('effect') == 'negative':
                triggers['negative_triggers'].append(trigger)

        return triggers

    def check_for_trigger(
        self,
        current_analysis: Dict,
        known_triggers: Dict
    ) -> Dict:
        """
        Check if current situation matches a known trigger.

        Args:
            current_analysis: Current analysis result
            known_triggers: Output from identify_triggers()

        Returns:
            Dict with:
            - triggered: bool
            - matched_triggers: List of matched triggers
            - predicted_impact: Expected emotional effect
        """
        text = current_analysis.get('text_analysis', {}).get('text', '').lower()
        timestamp = current_analysis.get('text_analysis', {}).get('timestamp')
        dt = parse_iso_timestamp(timestamp) or datetime.now()

        matched = []

        # Check event triggers
        for trigger in known_triggers.get('event_triggers', []):
            pattern = trigger.get('pattern')
            if pattern and re.search(pattern, text):
                matched.append(trigger)

        # Check keyword triggers
        for trigger in known_triggers.get('keyword_triggers', []):
            keyword = trigger.get('keyword')
            if keyword and keyword in text:
                matched.append(trigger)

        # Check temporal triggers
        for trigger in known_triggers.get('temporal_triggers', []):
            if trigger.get('hour') == dt.hour or trigger.get('weekday') == dt.weekday():
                matched.append(trigger)

        # Check social triggers
        for trigger in known_triggers.get('social_triggers', []):
            person = trigger.get('person')
            if person and person in text:
                matched.append(trigger)

        # Determine predicted impact
        if matched:
            # Average confidence of matched triggers
            avg_confidence = sum(t.get('confidence', 0) for t in matched) / len(matched)

            # Most common predicted emotion
            emotions = [t.get('emotion') for t in matched if t.get('emotion')]
            predicted_emotion = Counter(emotions).most_common(1)[0][0] if emotions else None

            return {
                'triggered': True,
                'matched_triggers': matched,
                'predicted_emotion': predicted_emotion,
                'confidence': round(avg_confidence, 3),
                'interpretation': self._interpret_triggers(matched)
            }

        return {
            'triggered': False,
            'matched_triggers': [],
            'predicted_emotion': None,
            'confidence': 0.0,
            'interpretation': 'No known triggers detected'
        }

    def _identify_event_triggers(self, entries: List[Dict], min_occ: int) -> List[Dict]:
        """Identify event-based triggers."""
        triggers = []

        for category, patterns in self.event_keywords.items():
            # Track when this event appears and what emotion follows
            event_emotions = []

            for entry in entries:
                text = entry.get('text', '').lower()
                emotion = entry.get('emotion_primary')

                if emotion:
                    for pattern in patterns:
                        if re.search(pattern, text):
                            event_emotions.append(emotion)
                            break

            # If event occurred enough times
            if len(event_emotions) >= min_occ:
                # Find most common emotion
                emotion_counts = Counter(event_emotions)
                most_common = emotion_counts.most_common(1)[0]

                confidence = most_common[1] / len(event_emotions)

                # Determine if positive or negative effect
                effect = 'positive' if most_common[0] in ['joy', 'calm', 'content'] else 'negative'

                triggers.append({
                    'type': 'event',
                    'category': category,
                    'pattern': patterns[0],
                    'emotion': most_common[0],
                    'occurrences': len(event_emotions),
                    'confidence': round(confidence, 3),
                    'effect': effect,
                    'description': f"{category} → {most_common[0]} ({most_common[1]}/{len(event_emotions)} times)"
                })

        return triggers

    def _identify_keyword_triggers(self, entries: List[Dict], min_occ: int) -> List[Dict]:
        """Identify specific keyword triggers."""
        # Extract all keywords and their associated emotions
        keyword_emotions = defaultdict(list)

        for entry in entries:
            keywords_json = entry.get('keywords_json')
            emotion = entry.get('emotion_primary')

            if keywords_json and emotion:
                try:
                    import json
                    keywords = json.loads(keywords_json) if isinstance(keywords_json, str) else keywords_json
                    for kw in keywords:
                        keyword_emotions[kw.lower()].append(emotion)
                except:
                    pass

        # Find keywords that consistently trigger specific emotions
        triggers = []

        for keyword, emotions in keyword_emotions.items():
            if len(emotions) >= min_occ:
                emotion_counts = Counter(emotions)
                most_common = emotion_counts.most_common(1)[0]

                confidence = most_common[1] / len(emotions)

                # Only include if confidence > 0.6 (strong association)
                if confidence >= 0.6:
                    effect = 'positive' if most_common[0] in ['joy', 'calm', 'content'] else 'negative'

                    triggers.append({
                        'type': 'keyword',
                        'keyword': keyword,
                        'emotion': most_common[0],
                        'occurrences': len(emotions),
                        'confidence': round(confidence, 3),
                        'effect': effect,
                        'description': f"'{keyword}' → {most_common[0]} ({confidence:.0%} of the time)"
                    })

        # Sort by confidence
        triggers.sort(key=lambda t: t['confidence'], reverse=True)

        return triggers[:10]  # Top 10 keyword triggers

    def _identify_temporal_triggers(self, entries: List[Dict], min_occ: int) -> List[Dict]:
        """Identify time-based triggers."""
        hour_emotions = defaultdict(list)
        weekday_emotions = defaultdict(list)

        for entry in entries:
            dt = parse_iso_timestamp(entry.get('timestamp'))
            if not dt:
                continue
            emotion = entry.get('emotion_primary')

            if emotion:
                hour_emotions[dt.hour].append(emotion)
                weekday_emotions[dt.weekday()].append(emotion)

        triggers = []

        # Hour-based triggers
        for hour, emotions in hour_emotions.items():
            if len(emotions) >= min_occ:
                emotion_counts = Counter(emotions)
                most_common = emotion_counts.most_common(1)[0]

                confidence = most_common[1] / len(emotions)

                if confidence >= 0.6:
                    effect = 'positive' if most_common[0] in ['joy', 'calm', 'content'] else 'negative'

                    triggers.append({
                        'type': 'temporal',
                        'hour': hour,
                        'emotion': most_common[0],
                        'occurrences': len(emotions),
                        'confidence': round(confidence, 3),
                        'effect': effect,
                        'description': f"{hour}:00 → {most_common[0]} ({confidence:.0%} of the time)"
                    })

        # Weekday-based triggers
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        for weekday, emotions in weekday_emotions.items():
            if len(emotions) >= min_occ:
                emotion_counts = Counter(emotions)
                most_common = emotion_counts.most_common(1)[0]

                confidence = most_common[1] / len(emotions)

                if confidence >= 0.6:
                    effect = 'positive' if most_common[0] in ['joy', 'calm', 'content'] else 'negative'

                    triggers.append({
                        'type': 'temporal',
                        'weekday': weekday,
                        'emotion': most_common[0],
                        'occurrences': len(emotions),
                        'confidence': round(confidence, 3),
                        'effect': effect,
                        'description': f"{days[weekday]}s → {most_common[0]} ({confidence:.0%} of the time)"
                    })

        return triggers

    def _identify_social_triggers(self, entries: List[Dict], min_occ: int) -> List[Dict]:
        """Identify people-based triggers."""
        person_emotions = defaultdict(list)

        for entry in entries:
            text = entry.get('text', '').lower()
            emotion = entry.get('emotion_primary')

            if emotion:
                for person in self.people_keywords:
                    if person in text:
                        person_emotions[person].append(emotion)

        triggers = []

        for person, emotions in person_emotions.items():
            if len(emotions) >= min_occ:
                emotion_counts = Counter(emotions)
                most_common = emotion_counts.most_common(1)[0]

                confidence = most_common[1] / len(emotions)

                if confidence >= 0.6:
                    effect = 'positive' if most_common[0] in ['joy', 'calm', 'content'] else 'negative'

                    triggers.append({
                        'type': 'social',
                        'person': person,
                        'emotion': most_common[0],
                        'occurrences': len(emotions),
                        'confidence': round(confidence, 3),
                        'effect': effect,
                        'description': f"Mentions of '{person}' → {most_common[0]} ({confidence:.0%} of the time)"
                    })

        return triggers

    def _identify_transition_triggers(self, entries: List[Dict], min_occ: int) -> List[Dict]:
        """
        Identify triggers that cause emotional transitions.

        Example: "talked to friend" → shift from sad to happy
        """
        triggers = []

        # Look for transitions (change in emotion between consecutive entries)
        for i in range(len(entries) - 1):
            current = entries[i]
            next_entry = entries[i + 1]

            current_emotion = current.get('emotion_primary')
            next_emotion = next_entry.get('emotion_primary')
            text = current.get('text', '').lower()

            # If emotion changed
            if current_emotion and next_emotion and current_emotion != next_emotion:
                # Check what keywords/events appeared
                for category, patterns in self.event_keywords.items():
                    for pattern in patterns:
                        if re.search(pattern, text):
                            # Record this as potential transition trigger
                            triggers.append({
                                'category': category,
                                'from': current_emotion,
                                'to': next_emotion
                            })

        # Find consistent transition triggers
        transition_counts = defaultdict(Counter)
        for t in triggers:
            key = (t['category'], t['from'], t['to'])
            transition_counts[key]['count'] += 1

        # Format results
        result_triggers = []
        for (category, from_emo, to_emo), data in transition_counts.items():
            count = data['count']
            if count >= min_occ:
                # Determine effect
                from_val = self._emotion_valence(from_emo)
                to_val = self._emotion_valence(to_emo)
                effect = 'positive' if to_val > from_val else 'negative'

                result_triggers.append({
                    'type': 'transition',
                    'category': category,
                    'from_emotion': from_emo,
                    'to_emotion': to_emo,
                    'occurrences': count,
                    'effect': effect,
                    'description': f"{category} → {from_emo} to {to_emo} shift ({count} times)"
                })

        return result_triggers

    def _emotion_valence(self, emotion: str) -> float:
        """Get emotional valence for comparison."""
        valence_map = {
            'joy': 1.0,
            'content': 0.7,
            'calm': 0.5,
            'neutral': 0.0,
            'anxiety': -0.3,
            'fear': -0.6,
            'sadness': -0.7,
            'anger': -0.8
        }
        return valence_map.get(emotion, 0.0)

    def _interpret_triggers(self, matched_triggers: List[Dict]) -> str:
        """Generate interpretation of matched triggers."""
        if not matched_triggers:
            return "No triggers detected"

        # Group by effect
        positive = [t for t in matched_triggers if t.get('effect') == 'positive']
        negative = [t for t in matched_triggers if t.get('effect') == 'negative']

        parts = []

        if positive:
            parts.append(f"{len(positive)} positive trigger(s) detected")
        if negative:
            parts.append(f"{len(negative)} negative trigger(s) detected")

        # List top triggers
        top_triggers = sorted(matched_triggers, key=lambda t: t.get('confidence', 0), reverse=True)[:2]
        trigger_desc = [t.get('description', '') for t in top_triggers]

        return f"{'; '.join(parts)}. Top: {'; '.join(trigger_desc)}"
