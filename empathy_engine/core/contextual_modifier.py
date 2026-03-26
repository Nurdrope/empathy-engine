"""
EmpathyEngine - Contextual Modifier System
Adjusts emotion interpretation based on situational context

Context changes everything:
- "I'm nervous" before a first date = excited anticipation
- "I'm nervous" before medical tests = health anxiety
- "I'm tired" after exercise = satisfied exhaustion
- "I'm tired" every morning = potential depression

This module detects context from:
- Time of day/week/year
- Mentioned events (work, relationships, health, etc.)
- Recent history (what happened before)
- Environmental factors (holidays, seasons)

Created: December 18, 2025
Part of the "all of them" expansion
"""

import re
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from collections import Counter
from ..utils.time import parse_iso_timestamp


class ContextualModifier:
    """
    Modifies emotional interpretation based on detected context.

    Context categories:
    - Temporal: Time of day, day of week, season, holidays
    - Event-based: Work, social, health, financial, family
    - Environmental: Weather mentions, location, physical state
    - Historical: Recent patterns, ongoing situations

    Usage:
        modifier = ContextualModifier()

        # Detect context and adjust interpretation
        contextualized = modifier.apply_context(
            analysis_result,
            recent_entries=historical_data
        )
        # Returns modified emotion with context notes
    """

    def __init__(self):
        # Event contexts
        self.work_keywords = [
            r'\b(work|job|boss|meeting|deadline|project|office|colleague|client|presentation)\b',
            r'\b(career|interview|promotion|fired|quit|resign)\b'
        ]

        self.social_keywords = [
            r'\b(friend|party|date|dating|relationship|breakup|fight|argument)\b',
            r'\b(social|lonely|alone|hanging out|going out)\b'
        ]

        self.health_keywords = [
            r'\b(doctor|hospital|sick|ill|pain|hurt|injury|medication|therapy|therapist)\b',
            r'\b(health|medical|surgery|diagnosis|symptom)\b'
        ]

        self.financial_keywords = [
            r'\b(money|bills|debt|broke|expensive|afford|budget|paycheck|rent|mortgage)\b',
            r'\b(financial|economy|job loss|unemployment)\b'
        ]

        self.family_keywords = [
            r'\b(mom|dad|mother|father|parent|child|kid|family|sibling|brother|sister)\b',
            r'\b(home|house|moving|divorce)\b'
        ]

        self.achievement_keywords = [
            r'\b(accomplish|achieve|success|win|won|passed|finished|completed|proud)\b',
            r'\b(goal|milestone|victory)\b'
        ]

        self.loss_keywords = [
            r'\b(lost|death|died|passed away|funeral|grief|mourning)\b',
            r'\b(goodbye|leaving|left|ended)\b'
        ]

        # Physical state contexts
        self.exercise_keywords = [
            r'\b(workout|exercise|gym|run|running|jog|yoga|lift|training|sport)\b'
        ]

        self.sleep_keywords = [
            r'\b(sleep|slept|insomnia|awake|tired|exhausted|nap|rest)\b'
        ]

        self.food_keywords = [
            r'\b(eat|eating|ate|hungry|food|meal|dinner|lunch|breakfast|diet)\b'
        ]

        # Temporal modifiers
        self.holidays = {
            'christmas': (12, 25),
            'new year': (1, 1),
            'valentine': (2, 14),
            'halloween': (10, 31),
            'thanksgiving': (11, 24),  # Approximate
        }

    def apply_context(
        self,
        analysis_result: Dict,
        recent_entries: Optional[List[Dict]] = None,
        user_timezone: Optional[str] = None
    ) -> Dict:
        """
        Apply contextual modifications to emotion analysis.

        Args:
            analysis_result: Output from EmpathyEngine.analyze()
            recent_entries: Optional recent historical entries for context
            user_timezone: Optional timezone for temporal context

        Returns:
            Dict with:
            - original_emotion: Original detected emotion
            - contextualized_emotion: Emotion with context applied
            - context_detected: List of detected contexts
            - modifications: List of applied modifications
            - confidence_adjustment: How much context changes confidence
        """
        text = analysis_result.get('text_analysis', {}).get('text', '')
        timestamp = analysis_result.get('text_analysis', {}).get('timestamp') or datetime.now().isoformat()

        if not text:
            return self._no_context(analysis_result)

        contexts_detected = []
        modifications = []
        confidence_adjustment = 0.0

        # Detect temporal context
        temporal = self._detect_temporal_context(timestamp)
        if temporal:
            contexts_detected.append(temporal)

        # Detect event contexts
        event_contexts = self._detect_event_contexts(text)
        contexts_detected.extend(event_contexts)

        # Detect physical state contexts
        physical_contexts = self._detect_physical_contexts(text)
        contexts_detected.extend(physical_contexts)

        # Detect historical context (if recent entries provided)
        if recent_entries:
            historical_context = self._detect_historical_context(
                analysis_result,
                recent_entries
            )
            if historical_context:
                contexts_detected.append(historical_context)

        # Apply contextual modifications
        original_emotion = analysis_result.get('primary_emotion', 'neutral')
        contextualized_emotion = original_emotion
        original_interpretation = None

        # Modify interpretation based on context
        for context in contexts_detected:
            mod = self._apply_modification(
                original_emotion,
                context,
                analysis_result
            )
            if mod:
                modifications.append(mod)
                if mod.get('reinterpret_as'):
                    contextualized_emotion = mod['reinterpret_as']
                if mod.get('confidence_boost'):
                    confidence_adjustment += mod['confidence_boost']

        return {
            'original_emotion': original_emotion,
            'contextualized_emotion': contextualized_emotion,
            'context_detected': contexts_detected,
            'modifications': modifications,
            'confidence_adjustment': round(confidence_adjustment, 3),
            'interpretation': self._generate_interpretation(
                original_emotion,
                contextualized_emotion,
                contexts_detected
            )
        }

    def _detect_temporal_context(self, timestamp: str) -> Optional[Dict]:
        """Detect time-based context."""
        dt = parse_iso_timestamp(timestamp)
        if not dt:
            return None

        contexts = []

        # Time of day
        hour = dt.hour
        if 5 <= hour < 12:
            contexts.append('morning')
        elif 12 <= hour < 17:
            contexts.append('afternoon')
        elif 17 <= hour < 21:
            contexts.append('evening')
        else:
            contexts.append('late_night')

        # Day of week
        day = dt.weekday()
        if day == 0:
            contexts.append('monday')
        elif day == 4:
            contexts.append('friday')
        elif day in [5, 6]:
            contexts.append('weekend')

        # Season (Northern Hemisphere)
        month = dt.month
        if month in [12, 1, 2]:
            contexts.append('winter')
        elif month in [3, 4, 5]:
            contexts.append('spring')
        elif month in [6, 7, 8]:
            contexts.append('summer')
        else:
            contexts.append('fall')

        # Check for holidays
        for holiday, (h_month, h_day) in self.holidays.items():
            if dt.month == h_month and abs(dt.day - h_day) <= 3:
                contexts.append(f'near_{holiday}')

        return {
            'type': 'temporal',
            'contexts': contexts,
            'timestamp': timestamp
        }

    def _detect_event_contexts(self, text: str) -> List[Dict]:
        """Detect event-based contexts from text."""
        text_lower = text.lower()
        detected = []

        # Check each event category
        if any(re.search(pattern, text_lower) for pattern in self.work_keywords):
            detected.append({'type': 'event', 'category': 'work'})

        if any(re.search(pattern, text_lower) for pattern in self.social_keywords):
            detected.append({'type': 'event', 'category': 'social'})

        if any(re.search(pattern, text_lower) for pattern in self.health_keywords):
            detected.append({'type': 'event', 'category': 'health'})

        if any(re.search(pattern, text_lower) for pattern in self.financial_keywords):
            detected.append({'type': 'event', 'category': 'financial'})

        if any(re.search(pattern, text_lower) for pattern in self.family_keywords):
            detected.append({'type': 'event', 'category': 'family'})

        if any(re.search(pattern, text_lower) for pattern in self.achievement_keywords):
            detected.append({'type': 'event', 'category': 'achievement'})

        if any(re.search(pattern, text_lower) for pattern in self.loss_keywords):
            detected.append({'type': 'event', 'category': 'loss'})

        return detected

    def _detect_physical_contexts(self, text: str) -> List[Dict]:
        """Detect physical state contexts."""
        text_lower = text.lower()
        detected = []

        if any(re.search(pattern, text_lower) for pattern in self.exercise_keywords):
            detected.append({'type': 'physical', 'category': 'exercise'})

        if any(re.search(pattern, text_lower) for pattern in self.sleep_keywords):
            detected.append({'type': 'physical', 'category': 'sleep'})

        if any(re.search(pattern, text_lower) for pattern in self.food_keywords):
            detected.append({'type': 'physical', 'category': 'food'})

        return detected

    def _detect_historical_context(
        self,
        current_analysis: Dict,
        recent_entries: List[Dict]
    ) -> Optional[Dict]:
        """Detect ongoing situations from recent history."""
        if not recent_entries:
            return None

        # Look at last 7 days
        cutoff = datetime.now() - timedelta(days=7)
        recent = []
        for entry in recent_entries:
            ts = parse_iso_timestamp(entry.get('timestamp'))
            if ts and ts >= cutoff:
                recent.append(entry)

        if not recent:
            return None

        # Check for ongoing negative patterns
        negative_count = sum(
            1 for e in recent
            if e.get('sentiment_compound', 0) < -0.3
        )

        if negative_count >= 4:
            return {
                'type': 'historical',
                'category': 'ongoing_distress',
                'duration_days': 7,
                'frequency': negative_count
            }

        # Check for recent positive trend
        positive_count = sum(
            1 for e in recent
            if e.get('sentiment_compound', 0) > 0.3
        )

        if positive_count >= 4:
            return {
                'type': 'historical',
                'category': 'positive_streak',
                'duration_days': 7,
                'frequency': positive_count
            }

        return None

    def _apply_modification(
        self,
        emotion: str,
        context: Dict,
        analysis: Dict
    ) -> Optional[Dict]:
        """
        Apply contextual modification to emotion.

        Returns modification dict or None if no modification needed.
        """
        context_type = context['type']
        sentiment = analysis.get('text_analysis', {}).get('sentiment_compound', 0)

        # Event-based modifications
        if context_type == 'event':
            category = context['category']

            # Work context + anxiety/stress = work stress (more specific)
            if category == 'work' and emotion in ['anxiety', 'fear', 'sadness']:
                return {
                    'context': 'work',
                    'modification': f"{emotion} → work-related {emotion}",
                    'note': 'Work context detected - emotion likely job-related',
                    'confidence_boost': 0.1
                }

            # Social context + joy = social connection (positive)
            if category == 'social' and emotion == 'joy':
                return {
                    'context': 'social',
                    'modification': 'joy → social connection joy',
                    'note': 'Social context - joy from connection',
                    'confidence_boost': 0.1
                }

            # Social context + sadness = loneliness/rejection
            if category == 'social' and emotion in ['sadness', 'anxiety']:
                return {
                    'context': 'social',
                    'modification': f"{emotion} → social {emotion}",
                    'note': 'Social context - possible loneliness or conflict',
                    'confidence_boost': 0.1
                }

            # Health context + anxiety = health anxiety
            if category == 'health' and emotion in ['anxiety', 'fear']:
                return {
                    'context': 'health',
                    'modification': f"{emotion} → health anxiety",
                    'reinterpret_as': 'health_anxiety',
                    'note': 'Health context - anxiety about well-being',
                    'confidence_boost': 0.15
                }

            # Achievement context + joy = accomplishment pride
            if category == 'achievement' and emotion in ['joy', 'surprise']:
                return {
                    'context': 'achievement',
                    'modification': f"{emotion} → pride/accomplishment",
                    'reinterpret_as': 'pride',
                    'note': 'Achievement context - feeling accomplished',
                    'confidence_boost': 0.2
                }

            # Loss context + sadness = grief
            if category == 'loss' and emotion in ['sadness', 'fear']:
                return {
                    'context': 'loss',
                    'modification': f"{emotion} → grief",
                    'reinterpret_as': 'grief',
                    'note': 'Loss context - processing grief',
                    'confidence_boost': 0.2
                }

        # Physical context modifications
        if context_type == 'physical':
            category = context['category']

            # Exercise + tired but positive sentiment = satisfied exhaustion
            if category == 'exercise' and 'tired' in analysis.get('text_analysis', {}).get('text', '').lower():
                if sentiment >= 0:
                    return {
                        'context': 'exercise',
                        'modification': 'tired → satisfied post-exercise fatigue',
                        'note': 'Exercise context - fatigue is positive',
                        'confidence_boost': 0.15
                    }

            # Sleep issues + negative = potential depression/anxiety indicator
            if category == 'sleep' and emotion in ['sadness', 'anxiety']:
                return {
                    'context': 'sleep',
                    'modification': f"{emotion} → sleep-related distress",
                    'note': 'Sleep context - rest issues affecting mood',
                    'confidence_boost': 0.1
                }

        # Temporal context modifications
        if context_type == 'temporal':
            contexts = context.get('contexts', [])

            # Monday + negative = "Monday blues"
            if 'monday' in contexts and emotion in ['sadness', 'anxiety']:
                return {
                    'context': 'temporal',
                    'modification': f"{emotion} → monday morning blues",
                    'note': 'Monday context - work week anticipation',
                    'confidence_boost': 0.05
                }

            # Late night + anxiety = possible insomnia/rumination
            if 'late_night' in contexts and emotion in ['anxiety', 'sadness']:
                return {
                    'context': 'temporal',
                    'modification': f"{emotion} → nighttime rumination",
                    'note': 'Late night context - overthinking pattern',
                    'confidence_boost': 0.1
                }

            # Weekend + joy = leisure enjoyment
            if 'weekend' in contexts and emotion == 'joy':
                return {
                    'context': 'temporal',
                    'modification': 'joy → weekend relaxation',
                    'note': 'Weekend context - leisure time enjoyment',
                    'confidence_boost': 0.05
                }

        # Historical context modifications
        if context_type == 'historical':
            category = context.get('category')

            if category == 'ongoing_distress':
                return {
                    'context': 'historical',
                    'modification': f"{emotion} → part of ongoing distress pattern",
                    'note': f"This emotion is part of a {context['duration_days']}-day difficult period",
                    'confidence_boost': 0.1
                }

            if category == 'positive_streak':
                return {
                    'context': 'historical',
                    'modification': f"{emotion} → part of positive trend",
                    'note': f"This is part of a {context['duration_days']}-day positive period",
                    'confidence_boost': 0.05
                }

        return None

    def _generate_interpretation(
        self,
        original: str,
        contextualized: str,
        contexts: List[Dict]
    ) -> str:
        """Generate human-readable interpretation."""
        if original == contextualized and not contexts:
            return f"Emotion: {original} (no additional context detected)"

        context_types = [c['type'] for c in contexts]
        context_str = ', '.join(set(context_types))

        if original != contextualized:
            return f"Emotion: {original} → {contextualized} (context: {context_str})"
        else:
            return f"Emotion: {original} (context: {context_str} provides additional nuance)"

    def _no_context(self, analysis: Dict) -> Dict:
        """Return structure when no context detected."""
        emotion = analysis.get('primary_emotion', 'neutral')

        return {
            'original_emotion': emotion,
            'contextualized_emotion': emotion,
            'context_detected': [],
            'modifications': [],
            'confidence_adjustment': 0.0,
            'interpretation': f"Emotion: {emotion} (no additional context)"
        }
