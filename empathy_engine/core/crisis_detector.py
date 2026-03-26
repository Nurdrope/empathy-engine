"""
EmpathyEngine - Crisis & Risk Detection Module
Detects emotional crisis signals and mental health risk factors

IMPORTANT DISCLAIMER:
This module is a support tool, NOT a replacement for professional mental health care.
All crisis detection should trigger recommendations to seek professional help.

Crisis indicators:
- Self-harm language
- Suicidal ideation keywords
- Extreme hopelessness/despair
- Severe anxiety/panic
- Loss of control language
- Isolation/withdrawal patterns
- Substance abuse mentions

Created: December 18, 2025
Part of the "all of them" expansion
"""

import re
from typing import Dict, Optional, List, Tuple
from datetime import datetime, timedelta
from collections import Counter
from ..utils.time import parse_iso_timestamp


class CrisisDetector:
    """
    Detects emotional crisis and mental health risk signals.

    **CRITICAL**: This is a screening tool, not a diagnostic tool.
    Always recommend professional support when crisis detected.

    Risk levels:
    - IMMEDIATE: Urgent crisis (self-harm, suicidal ideation) → immediate intervention
    - HIGH: Severe distress → professional help needed soon
    - MODERATE: Concerning patterns → suggest support resources
    - LOW: Normal distress → monitor

    Usage:
        detector = CrisisDetector()
        risk = detector.assess_risk(analysis_result, entries=historical_data)
        if risk['level'] == 'IMMEDIATE':
            # Trigger crisis protocol
    """

    def __init__(self):
        # IMMEDIATE RISK - Suicidal ideation
        self.suicide_keywords = [
            r'\bkill myself\b',
            r'\bend (it|my life|everything)\b',
            r'\bsuicide\b',
            r'\bdon\'t want to (live|be here|exist)\b',
            r'\bbetter off dead\b',
            r'\bno reason to live\b',
            r'\bcan\'t go on\b',
            r'\bwant to die\b',
            r'\btake my (own )?life\b',
            r'\bno point (in )?(living|going on)\b'
        ]

        # IMMEDIATE RISK - Self-harm
        self.self_harm_keywords = [
            r'\bcut(ting)? myself\b',
            r'\bhurt(ing)? myself\b',
            r'\bself[- ]harm\b',
            r'\bburn(ing)? myself\b',
            r'\bpunish myself\b',
            r'\bdeserve (pain|to suffer|to hurt)\b'
        ]

        # HIGH RISK - Hopelessness/despair
        self.hopelessness_keywords = [
            r'\bno hope\b',
            r'\bhopeless\b',
            r'\bnothing (will|can) (change|help|get better)\b',
            r'\bpointless\b',
            r'\bno future\b',
            r'\bgive up\b',
            r'\bcan\'t take (it|this) anymore\b',
            r'\bno way out\b',
            r'\btrapped\b',
            r'\bstuck forever\b'
        ]

        # HIGH RISK - Severe anxiety/panic
        self.panic_keywords = [
            r'\bcan\'t breathe\b',
            r'\bpanic attack\b',
            r'\bloss of control\b',
            r'\bgoing crazy\b',
            r'\blosing my mind\b',
            r'\bcan\'t function\b',
            r'\bcompletely overwhelmed\b',
            r'\bbreaking down\b',
            r'\bfalling apart\b'
        ]

        # MODERATE RISK - Isolation/withdrawal
        self.isolation_keywords = [
            r'\b(don\'t|can\'t) talk to anyone\b',
            r'\bno one (cares|understands)\b',
            r'\ball alone\b',
            r'\bisolat(ed|ing)\b',
            r'\bhiding (from|away)\b',
            r'\bpushing (people|everyone) away\b',
            r'\bavoid(ing)? everyone\b',
            r'\bno (friends|support)\b'
        ]

        # MODERATE RISK - Loss of interest/motivation
        self.anhedonia_keywords = [
            r'\bdon\'t care anymore\b',
            r'\bnothing matters\b',
            r'\blost interest\b',
            r'\bcan\'t (feel|enjoy) anything\b',
            r'\bnumb\b',
            r'\bempty inside\b',
            r'\bwhat\'s the point\b'
        ]

        # MODERATE RISK - Substance mentions
        self.substance_keywords = [
            r'\bdrinking (heavily|too much|every day)\b',
            r'\busing (drugs|pills)\b',
            r'\bself[- ]medicat(e|ing)\b',
            r'\bneed (alcohol|drugs) to (cope|function|sleep)\b',
            r'\bblacking out\b'
        ]

        # Crisis resources (to include in recommendations)
        self.crisis_resources = {
            'US': {
                'suicide_prevention': '988 Suicide & Crisis Lifeline',
                'crisis_text': 'Text HOME to 741741 (Crisis Text Line)',
                'emergency': '911'
            },
            'international': {
                'suicide_prevention': 'findahelpline.com',
                'crisis_text': 'Crisis Text Line (varies by country)'
            }
        }

    def assess_risk(
        self,
        analysis_result: Dict,
        entries: Optional[List[Dict]] = None,
        days: int = 30
    ) -> Dict:
        """
        Assess crisis/risk level from current analysis and historical data.

        Args:
            analysis_result: Output from EmpathyEngine.analyze()
            entries: Optional historical entries for pattern analysis
            days: Number of days of history to analyze

        Returns:
            Dict with:
            - level: str ('IMMEDIATE', 'HIGH', 'MODERATE', 'LOW')
            - score: float 0-1 (risk intensity)
            - indicators: List of detected risk factors
            - patterns: Optional historical patterns (if entries provided)
            - recommendations: List of recommended actions
            - resources: Crisis support resources
        """
        core = self._assess_core(analysis_result, entries=entries, days=days)
        level = core['level']
        indicators = core['indicators']
        patterns = core['patterns']
        risk_score = core['score']

        if core['no_risk']:
            return self._no_risk()

        # Generate recommendations
        recommendations = self._generate_recommendations(level, indicators, patterns)

        # Get crisis resources
        resources = self._get_resources(level)

        return {
            'level': level,
            'score': round(risk_score, 3),
            'indicators': indicators,
            'patterns': patterns,
            'recommendations': recommendations,
            'resources': resources,
            'timestamp': datetime.now().isoformat()
        }

    def assess_risk_schema(
        self,
        analysis_result: Dict,
        entries: Optional[List[Dict]] = None,
        days: int = 30
    ) -> Dict:
        """
        Assess crisis/risk level and return a tiered schema (alpha-wide open).

        Returns:
            Dict with:
            - risk_assessment: tiered summary + signals
            - user_view: minimal status (placeholder for v1.0 split)
            - clinical_view: full signals and raw inputs (placeholder for v1.0 split)
        """
        core = self._assess_core(analysis_result, entries=entries, days=days)
        text_analysis = analysis_result.get('text_analysis', {})
        text = text_analysis.get('text', '')

        if core['no_risk']:
            return {
                'risk_assessment': {
                    'tier': 'none',
                    'confidence': 0.0,
                    'signals': {
                        'lexical_hits': [],
                        'temporal_spike': False,
                        'baseline_deviation': 0.0,
                        'avoidance_detected': False,
                        'negative_short_count': 0
                    },
                    'notes': 'No risk indicators detected.'
                },
                'user_view': {
                    'status': 'neutral',
                    'summary': 'No risk indicators detected.'
                },
                'clinical_view': {
                    'signals': {},
                    'scores': {},
                    'timestamps': [],
                    'inputs': {'text': text}
                }
            }

        patterns = core['patterns'] or {}
        temporal_spike = bool(
            patterns.get('sudden_negative_shift', {}).get('detected')
            or patterns.get('escalating_distress', {}).get('detected')
        )
        baseline_deviation = float(patterns.get('baseline_deviation', 0.0) or 0.0)
        negative_short_count = int(patterns.get('negative_short_count', 0) or 0)
        avoidance_detected = self._detect_avoidance(text)

        tier = self._level_to_tier(core['level'])
        confidence = round(core['score'], 3)

        return {
            'risk_assessment': {
                'tier': tier,
                'confidence': confidence,
                'signals': {
                    'lexical_hits': core['indicators'],
                    'temporal_spike': temporal_spike,
                    'baseline_deviation': baseline_deviation,
                    'avoidance_detected': avoidance_detected,
                    'negative_short_count': negative_short_count
                },
                'notes': 'Auto-assessed risk signals (alpha, no user-facing advice).'
            },
            'user_view': {
                'status': self._tier_to_user_status(tier),
                'summary': 'Risk signals logged.'
            },
            'clinical_view': {
                'signals': {
                    'level': core['level'],
                    'indicators': core['indicators'],
                    'patterns': patterns
                },
                'scores': {'risk_score': core['score']},
                'timestamps': [datetime.now().isoformat()],
                'inputs': {'text': text}
            }
        }

    def _assess_core(
        self,
        analysis_result: Dict,
        entries: Optional[List[Dict]] = None,
        days: int = 30
    ) -> Dict:
        """Core risk scoring without recommendations/resources."""
        text_analysis = analysis_result.get('text_analysis', {})
        text = text_analysis.get('text', '')

        if not text:
            return {
                'no_risk': True,
                'level': 'LOW',
                'score': 0.0,
                'indicators': [],
                'patterns': None
            }

        indicators = []
        risk_score = 0.0
        level = 'LOW'

        immediate_risk = self._check_immediate_risk(text)
        if immediate_risk:
            indicators.extend(immediate_risk)
            risk_score = 1.0
            level = 'IMMEDIATE'
        else:
            high_risk = self._check_high_risk(text, analysis_result)
            if high_risk:
                indicators.extend(high_risk)
                risk_score = max(risk_score, 0.75)
                level = 'HIGH'

            moderate_risk = self._check_moderate_risk(text, analysis_result)
            if moderate_risk:
                indicators.extend(moderate_risk)
                risk_score = max(risk_score, 0.5)
                if level == 'LOW':
                    level = 'MODERATE'

        patterns = None
        if entries:
            patterns = self._analyze_historical_risk(entries, days)
            if patterns.get('escalating_distress', {}).get('detected'):
                risk_score = min(1.0, risk_score + 0.2)
                if level == 'LOW':
                    level = 'MODERATE'
            if patterns.get('prolonged_crisis', {}).get('detected'):
                risk_score = min(1.0, risk_score + 0.3)
                if level in ['LOW', 'MODERATE']:
                    level = 'HIGH'

        return {
            'no_risk': False,
            'level': level,
            'score': round(risk_score, 3),
            'indicators': indicators,
            'patterns': patterns
        }

    def _level_to_tier(self, level: str) -> str:
        """Map legacy levels to schema tiers."""
        return {
            'IMMEDIATE': 'critical',
            'HIGH': 'high',
            'MODERATE': 'concern',
            'LOW': 'monitor'
        }.get(level, 'none')

    def _tier_to_user_status(self, tier: str) -> str:
        """Map tier to minimal user-facing status (alpha placeholder)."""
        return {
            'critical': 'urgent',
            'high': 'concern',
            'concern': 'watch',
            'monitor': 'neutral',
            'none': 'neutral'
        }.get(tier, 'neutral')

    def _detect_avoidance(self, text: str) -> bool:
        """Simple avoidance detection for schema signals."""
        if not text or not text.strip():
            return False
        text_lower = text.lower().strip()
        word_count = len(text.split())
        avoidance_patterns = [
            'fine', 'im fine', "i'm fine", 'i am fine',
            'ok', 'okay', "i'm ok", 'im ok', 'i am ok',
            'whatever', 'nothing', 'nevermind', 'never mind',
            'idk', "i don't know", 'dont know',
            'same', 'same as usual', 'normal',
            'alright', "i'm alright", 'im alright',
            'good', "i'm good", 'im good',
            'meh', 'eh', 'sure', 'i guess'
        ]
        if word_count <= 5:
            for pattern in avoidance_patterns:
                if text_lower == pattern or text_lower.startswith(pattern + '.') or text_lower.startswith(pattern + '!'):
                    return True
        return False

    def _check_immediate_risk(self, text: str) -> List[str]:
        """Check for immediate crisis (suicide/self-harm)."""
        text_lower = text.lower()
        indicators = []

        # Suicide keywords
        for pattern in self.suicide_keywords:
            if re.search(pattern, text_lower):
                indicators.append(f"CRITICAL: Suicidal ideation detected - '{re.search(pattern, text_lower).group()}'")

        # Self-harm keywords
        for pattern in self.self_harm_keywords:
            if re.search(pattern, text_lower):
                indicators.append(f"CRITICAL: Self-harm language - '{re.search(pattern, text_lower).group()}'")

        return indicators

    def _check_high_risk(self, text: str, analysis_result: Dict) -> List[str]:
        """Check for high risk factors (hopelessness, severe panic)."""
        text_lower = text.lower()
        indicators = []

        # Hopelessness
        for pattern in self.hopelessness_keywords:
            if re.search(pattern, text_lower):
                indicators.append(f"Severe hopelessness: '{re.search(pattern, text_lower).group()}'")

        # Panic/loss of control
        for pattern in self.panic_keywords:
            if re.search(pattern, text_lower):
                indicators.append(f"Severe anxiety/panic: '{re.search(pattern, text_lower).group()}'")

        # Very negative sentiment + fear/anxiety
        sentiment = analysis_result.get('text_analysis', {}).get('sentiment_compound', 0)
        emotion = analysis_result.get('primary_emotion', 'neutral')
        if sentiment < -0.7 and emotion in ['fear', 'anxiety', 'sadness']:
            indicators.append(f"Extreme negative emotion: {emotion} with very low sentiment ({sentiment:.2f})")

        return indicators

    def _check_moderate_risk(self, text: str, analysis_result: Dict) -> List[str]:
        """Check for moderate risk factors (isolation, anhedonia, substances)."""
        text_lower = text.lower()
        indicators = []

        # Isolation
        for pattern in self.isolation_keywords:
            if re.search(pattern, text_lower):
                indicators.append(f"Social isolation: '{re.search(pattern, text_lower).group()}'")

        # Anhedonia/loss of interest
        for pattern in self.anhedonia_keywords:
            if re.search(pattern, text_lower):
                indicators.append(f"Loss of interest/motivation: '{re.search(pattern, text_lower).group()}'")

        # Substance use
        for pattern in self.substance_keywords:
            if re.search(pattern, text_lower):
                indicators.append(f"Substance use concern: '{re.search(pattern, text_lower).group()}'")

        return indicators

    def _analyze_historical_risk(self, entries: List[Dict], days: int) -> Dict:
        """
        Analyze historical entries for concerning patterns.

        Patterns to detect:
        - Escalating distress (worsening over time)
        - Prolonged crisis (persistent severe negativity)
        - Sudden change (abrupt shift to very negative)
        - Increasing isolation
        """
        from datetime import datetime, timedelta

        now = datetime.now()
        cutoff = now - timedelta(days=days)

        # Filter to time window
        recent_entries = []
        for entry in entries:
            ts = parse_iso_timestamp(entry.get('timestamp'))
            if ts and ts >= cutoff:
                recent_entries.append(entry)

        if not recent_entries:
            return {}

        # Sort by timestamp
        recent_entries.sort(key=lambda e: e.get('timestamp') or "")

        # Track sentiment over time
        sentiments = []
        for e in recent_entries:
            sent = e.get('sentiment_compound', 0)
            ts = parse_iso_timestamp(e.get('timestamp'))
            if ts:
                sentiments.append((ts, sent))

        patterns = {}

        # Detect escalating distress (sentiment getting more negative)
        if len(sentiments) >= 5:
            first_half_avg = sum([s for _, s in sentiments[:len(sentiments)//2]]) / (len(sentiments)//2)
            second_half_avg = sum([s for _, s in sentiments[len(sentiments)//2:]]) / (len(sentiments) - len(sentiments)//2)

            if second_half_avg < first_half_avg - 0.3:
                patterns['escalating_distress'] = {
                    'detected': True,
                    'change': round(second_half_avg - first_half_avg, 2),
                    'description': 'Emotional state worsening over time'
                }

        # Detect prolonged crisis (many very negative entries)
        very_negative_count = sum(1 for _, s in sentiments if s < -0.5)
        if very_negative_count >= 5:
            patterns['prolonged_crisis'] = {
                'detected': True,
                'count': very_negative_count,
                'description': f'{very_negative_count} entries with severe negativity in past {days} days'
            }

        # Detect sudden change (abrupt drop)
        if len(sentiments) >= 3:
            recent_3_avg = sum([s for _, s in sentiments[-3:]]) / 3
            if recent_3_avg < -0.6:
                patterns['sudden_negative_shift'] = {
                    'detected': True,
                    'avg_sentiment': round(recent_3_avg, 2),
                    'description': 'Recent sharp decline in emotional state'
                }

        # Detect isolation mentions
        isolation_count = sum(
            1 for e in recent_entries
            if any(re.search(pattern, e.get('text', '').lower()) for pattern in self.isolation_keywords)
        )
        if isolation_count >= 3:
            patterns['increasing_isolation'] = {
                'detected': True,
                'count': isolation_count,
                'description': f'{isolation_count} mentions of isolation/loneliness'
            }

        # Count short negative entries
        negative_short_count = 0
        for entry in recent_entries:
            text = entry.get('text', '') or ''
            if not text or len(text.split()) >= 15:
                continue
            sentiment = entry.get('sentiment_compound')
            if sentiment is not None and sentiment <= -0.3:
                negative_short_count += 1
        patterns['negative_short_count'] = negative_short_count

        return patterns

    def _generate_recommendations(
        self,
        level: str,
        indicators: List[str],
        patterns: Optional[Dict]
    ) -> List[str]:
        """Generate appropriate recommendations based on risk level."""
        recommendations = []

        if level == 'IMMEDIATE':
            recommendations.append("🚨 IMMEDIATE ACTION REQUIRED")
            recommendations.append("Contact crisis support NOW: 988 Suicide & Crisis Lifeline (US)")
            recommendations.append("Or text HOME to 741741 (Crisis Text Line)")
            recommendations.append("If in immediate danger, call 911 (US) or local emergency services")
            recommendations.append("You are not alone - professional help is available 24/7")

        elif level == 'HIGH':
            recommendations.append("⚠️ HIGH PRIORITY: Seek professional support soon")
            recommendations.append("Contact a mental health professional or therapist")
            recommendations.append("Reach out to a trusted friend or family member")
            recommendations.append("Consider crisis support: 988 (US) or Crisis Text Line")
            recommendations.append("Avoid being alone if possible")

        elif level == 'MODERATE':
            recommendations.append("⚠️ Concerning patterns detected")
            recommendations.append("Consider talking to a counselor or therapist")
            recommendations.append("Reach out to supportive friends/family")
            recommendations.append("Practice self-care and stress reduction")
            recommendations.append("Monitor your emotional state closely")

        else:  # LOW
            recommendations.append("Continue monitoring your emotional well-being")
            recommendations.append("Maintain social connections")
            recommendations.append("Practice healthy coping strategies")

        return recommendations

    def _get_resources(self, level: str) -> Dict:
        """Get appropriate crisis resources based on risk level."""
        if level in ['IMMEDIATE', 'HIGH']:
            return {
                'crisis_hotline': '988 Suicide & Crisis Lifeline (US)',
                'crisis_text': 'Text HOME to 741741',
                'emergency': '911 (US)',
                'international': 'findahelpline.com',
                'online_chat': 'suicidepreventionlifeline.org/chat'
            }
        elif level == 'MODERATE':
            return {
                'therapy': 'betterhelp.com, talkspace.com (online therapy)',
                'support_groups': 'NAMI.org (mental health support)',
                'crisis_text': 'Text HOME to 741741 if needed',
                'warmline': 'warmline.org (non-crisis peer support)'
            }
        else:
            return {
                'mental_health_resources': 'mentalhealth.gov',
                'self_help': 'NAMI.org, mind.org.uk'
            }

    def _no_risk(self) -> Dict:
        """Return structure for no risk detected."""
        return {
            'level': 'LOW',
            'score': 0.0,
            'indicators': [],
            'patterns': None,
            'recommendations': ['No crisis indicators detected'],
            'resources': {},
            'timestamp': datetime.now().isoformat()
        }

    def assess_batch(self, analysis_results: List[Dict]) -> List[Dict]:
        """
        Assess risk for multiple analysis results.

        Args:
            analysis_results: List of analysis result dicts

        Returns:
            List of risk assessment results
        """
        return [self.assess_risk(result) for result in analysis_results]

    def get_risk_summary(self, assessment: Dict) -> str:
        """
        Generate human-readable risk summary.

        Args:
            assessment: Output from assess_risk()

        Returns:
            Summary like "HIGH RISK (0.75) - Immediate support recommended"
        """
        level = assessment['level']
        score = assessment['score']

        if level == 'IMMEDIATE':
            return f"🚨 {level} RISK ({score:.2f}) - CRISIS INTERVENTION NEEDED"
        elif level == 'HIGH':
            return f"⚠️ {level} RISK ({score:.2f}) - Professional support recommended"
        elif level == 'MODERATE':
            return f"⚠️ {level} RISK ({score:.2f}) - Consider seeking support"
        else:
            return f"✓ {level} RISK ({score:.2f}) - No immediate concerns"
