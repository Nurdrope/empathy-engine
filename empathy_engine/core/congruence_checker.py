"""
EmpathyEngine - Emotion Congruence Checker
Validates emotional coherence across multiple dimensions

This module checks if all emotional signals align:
- Text sentiment ↔ Detected emotion (do words match feeling?)
- Voice prosody ↔ Text emotion (does tone match words?)
- Intensity ↔ Language (do strong words match strong emotion?)
- Context ↔ Emotion (does situation explain feeling?)
- Time pattern ↔ Current state (is this normal for this time?)

High congruence = authentic, clear emotional state
Low congruence = confusion, masking, or complex mixed emotions

Created: December 18, 2025
Part of the "all of them" expansion
"""

from typing import Dict, Optional, List, Tuple
import numpy as np


class CongruenceChecker:
    """
    Checks emotional congruence across multiple dimensions.

    Congruence dimensions:
    1. Sentiment-Emotion alignment
    2. Voice-Text alignment (if voice available)
    3. Intensity-Language alignment
    4. Context-Emotion alignment
    5. Historical pattern alignment

    Congruence score:
    - 0.8-1.0: High congruence (clear, authentic state)
    - 0.5-0.8: Moderate congruence (some mixed signals)
    - 0.0-0.5: Low congruence (conflicting signals, possible masking)

    Usage:
        checker = CongruenceChecker()

        congruence = checker.check_congruence(
            analysis_result,
            intensity_result=intensity,
            context_result=context,
            baseline=baseline_profile
        )
        # Returns: {'score': 0.85, 'dimensions': [...], 'interpretation': '...'}
    """

    def __init__(self):
        # Expected sentiment ranges for each emotion
        self.emotion_sentiment_map = {
            'joy': (0.3, 1.0),
            'surprise': (-0.2, 0.8),  # Can be positive or negative
            'neutral': (-0.2, 0.2),
            'anxiety': (-0.6, 0.0),
            'fear': (-0.8, -0.2),
            'sadness': (-0.9, -0.2),
            'anger': (-0.9, -0.3),
            'disgust': (-0.9, -0.4),
            # Additional emotions
            'calm': (0.0, 0.5),
            'excited': (0.4, 1.0),
            'frustrated': (-0.7, -0.2),
            'content': (0.2, 0.7)
        }

        # Expected intensity ranges for strong emotion words
        self.strong_words = [
            'extremely', 'incredibly', 'absolutely', 'devastated', 'ecstatic',
            'furious', 'terrified', 'overwhelmed', 'thrilled', 'horrible',
            'amazing', 'worst', 'best', 'love', 'hate'
        ]

    def check_congruence(
        self,
        analysis_result: Dict,
        intensity_result: Optional[Dict] = None,
        context_result: Optional[Dict] = None,
        baseline: Optional[Dict] = None,
        sarcasm_result: Optional[Dict] = None
    ) -> Dict:
        """
        Check emotional congruence across all available dimensions.

        Args:
            analysis_result: Output from EmpathyEngine.analyze()
            intensity_result: Optional output from IntensityCalibrator
            context_result: Optional output from ContextualModifier
            baseline: Optional baseline profile from BaselineProfiler
            sarcasm_result: Optional output from SarcasmDetector

        Returns:
            Dict with:
            - score: float 0-1 (overall congruence)
            - level: 'high', 'moderate', or 'low'
            - dimensions: List of dimension checks
            - alerts: List of incongruence alerts
            - interpretation: Human-readable summary
        """
        dimension_scores = []
        alerts = []

        # Dimension 1: Sentiment-Emotion alignment
        sentiment_emotion = self._check_sentiment_emotion(analysis_result)
        dimension_scores.append(sentiment_emotion['score'])
        if not sentiment_emotion['aligned']:
            alerts.append(sentiment_emotion)

        # Dimension 2: Voice-Text alignment (if voice available)
        if analysis_result.get('voice_analysis'):
            voice_text = self._check_voice_text(analysis_result)
            dimension_scores.append(voice_text['score'])
            if not voice_text['aligned']:
                alerts.append(voice_text)

        # Dimension 3: Intensity-Language alignment (if intensity available)
        if intensity_result:
            intensity_language = self._check_intensity_language(
                analysis_result,
                intensity_result
            )
            dimension_scores.append(intensity_language['score'])
            if not intensity_language['aligned']:
                alerts.append(intensity_language)

        # Dimension 4: Context-Emotion alignment (if context available)
        if context_result:
            context_emotion = self._check_context_emotion(
                analysis_result,
                context_result
            )
            dimension_scores.append(context_emotion['score'])
            if not context_emotion['aligned']:
                alerts.append(context_emotion)

        # Dimension 5: Baseline alignment (if baseline available)
        if baseline:
            baseline_align = self._check_baseline_alignment(
                analysis_result,
                baseline
            )
            dimension_scores.append(baseline_align['score'])
            if not baseline_align['aligned']:
                alerts.append(baseline_align)

        # Dimension 6: Sarcasm check (lowers congruence if detected)
        if sarcasm_result and sarcasm_result.get('sarcasm_detected'):
            sarcasm_check = {
                'dimension': 'sarcasm',
                'score': 0.3,  # Sarcasm means low congruence
                'aligned': False,
                'note': f"Sarcasm detected ({sarcasm_result['confidence']:.0%}) - stated emotion may not match true feeling"
            }
            dimension_scores.append(0.3)
            alerts.append(sarcasm_check)

        # Calculate overall congruence score
        if dimension_scores:
            overall_score = np.mean(dimension_scores)
        else:
            overall_score = 0.5  # Default if no dimensions available

        # Determine congruence level
        if overall_score >= 0.8:
            level = 'high'
        elif overall_score >= 0.5:
            level = 'moderate'
        else:
            level = 'low'

        # Generate interpretation
        interpretation = self._generate_interpretation(
            overall_score,
            level,
            alerts,
            len(dimension_scores)
        )

        return {
            'score': round(overall_score, 3),
            'level': level,
            'dimensions_checked': len(dimension_scores),
            'dimensions': dimension_scores,
            'alerts': alerts,
            'interpretation': interpretation
        }

    def _check_sentiment_emotion(self, analysis: Dict) -> Dict:
        """
        Check if sentiment score matches detected emotion.

        Example: If emotion is 'joy', sentiment should be positive
        """
        emotion = analysis.get('primary_emotion', 'neutral')
        sentiment = analysis.get('text_analysis', {}).get('sentiment_compound', 0)

        expected_range = self.emotion_sentiment_map.get(emotion, (-1, 1))
        min_sent, max_sent = expected_range

        # Check if sentiment falls in expected range
        aligned = min_sent <= sentiment <= max_sent

        # Calculate score based on how well it fits
        if aligned:
            # How centered in the range?
            range_center = (min_sent + max_sent) / 2
            deviation = abs(sentiment - range_center)
            range_size = max_sent - min_sent
            score = 1.0 - (deviation / (range_size / 2))
        else:
            # How far outside the range?
            if sentiment < min_sent:
                score = max(0, 1 - abs(sentiment - min_sent))
            else:
                score = max(0, 1 - abs(sentiment - max_sent))

        return {
            'dimension': 'sentiment_emotion',
            'score': max(0.0, min(1.0, score)),
            'aligned': aligned,
            'note': f"Emotion '{emotion}' expects sentiment {expected_range}, got {sentiment:.2f}"
        }

    def _check_voice_text(self, analysis: Dict) -> Dict:
        """
        Check if voice prosody matches text emotion.

        Uses the existing 'agreement' field from fusion.
        """
        agreement = analysis.get('agreement')
        authenticity = analysis.get('authenticity_score', 0.5)

        if agreement is None:
            return {
                'dimension': 'voice_text',
                'score': 0.5,
                'aligned': True,
                'note': 'Voice data available but no agreement calculated'
            }

        aligned = agreement
        score = authenticity  # Authenticity already factors in agreement

        return {
            'dimension': 'voice_text',
            'score': score,
            'aligned': aligned,
            'note': f"Voice and text {'agree' if aligned else 'disagree'} (authenticity: {authenticity:.2f})"
        }

    def _check_intensity_language(
        self,
        analysis: Dict,
        intensity_result: Dict
    ) -> Dict:
        """
        Check if emotional intensity matches language strength.

        Example: "I'm EXTREMELY angry!!!" should have high intensity
        """
        text = analysis.get('text_analysis', {}).get('text', '').lower()
        intensity = intensity_result.get('intensity', 0.5)

        # Check for strong language
        strong_word_count = sum(1 for word in self.strong_words if word in text)
        caps_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)
        exclamation_count = text.count('!')

        # Expected intensity based on language
        expected_intensity = 0.5  # Default
        if strong_word_count >= 2 or caps_ratio > 0.3 or exclamation_count >= 3:
            expected_intensity = 0.8  # Strong language → high intensity
        elif strong_word_count == 1 or caps_ratio > 0.1 or exclamation_count >= 1:
            expected_intensity = 0.6  # Moderate language → moderate intensity

        # Check alignment
        deviation = abs(intensity - expected_intensity)
        aligned = deviation < 0.3
        score = 1.0 - deviation

        return {
            'dimension': 'intensity_language',
            'score': max(0.0, min(1.0, score)),
            'aligned': aligned,
            'note': f"Language suggests {expected_intensity:.1f} intensity, measured {intensity:.2f}"
        }

    def _check_context_emotion(
        self,
        analysis: Dict,
        context_result: Dict
    ) -> Dict:
        """
        Check if detected emotion makes sense given context.

        Example: "Work context + anxiety" is congruent
        """
        emotion = analysis.get('primary_emotion', 'neutral')
        contexts = context_result.get('context_detected', [])

        if not contexts:
            return {
                'dimension': 'context_emotion',
                'score': 0.5,
                'aligned': True,
                'note': 'No specific context detected'
            }

        # Check if context explains emotion
        congruent_pairs = {
            ('work', 'anxiety'),
            ('work', 'stress'),
            ('work', 'frustration'),
            ('social', 'joy'),
            ('social', 'anxiety'),
            ('health', 'fear'),
            ('health', 'anxiety'),
            ('achievement', 'joy'),
            ('achievement', 'pride'),
            ('loss', 'sadness'),
            ('loss', 'grief'),
            ('exercise', 'tired'),
            ('exercise', 'satisfied'),
        }

        # Check each context
        matches = 0
        total = 0

        for ctx in contexts:
            if ctx.get('type') == 'event':
                category = ctx.get('category')
                total += 1
                if (category, emotion) in congruent_pairs:
                    matches += 1

        if total == 0:
            score = 0.5
            aligned = True
            note = "No event contexts to validate against"
        else:
            score = matches / total
            aligned = score >= 0.5
            note = f"{matches}/{total} contexts align with {emotion}"

        return {
            'dimension': 'context_emotion',
            'score': score,
            'aligned': aligned,
            'note': note
        }

    def _check_baseline_alignment(
        self,
        analysis: Dict,
        baseline: Dict
    ) -> Dict:
        """
        Check if current emotion aligns with user's baseline.

        Not checking for deviation (that's BaselineProfiler's job),
        but checking if the emotion is REALISTIC for this user.
        """
        if not baseline.get('metadata', {}).get('sufficient_data'):
            return {
                'dimension': 'baseline',
                'score': 0.5,
                'aligned': True,
                'note': 'Insufficient baseline data'
            }

        emotion = analysis.get('primary_emotion', 'neutral')
        emotion_dist = baseline.get('emotions', {}).get('distribution', {})

        # Check if this emotion ever appears in baseline
        if emotion in emotion_dist:
            frequency = emotion_dist[emotion]
            # More frequent = more aligned (user expresses this often)
            score = min(1.0, frequency * 3)  # Scale up
            aligned = True
            note = f"{emotion} is {frequency:.0%} of your baseline emotions"
        else:
            # Emotion never seen before
            score = 0.3
            aligned = False
            note = f"{emotion} is unusual - not in your typical emotional range"

        return {
            'dimension': 'baseline',
            'score': score,
            'aligned': aligned,
            'note': note
        }

    def _generate_interpretation(
        self,
        score: float,
        level: str,
        alerts: List[Dict],
        dimensions: int
    ) -> str:
        """Generate human-readable interpretation."""
        if level == 'high':
            interpretation = f"✓ High emotional congruence ({score:.0%}) - All signals align, suggesting authentic emotional state."
        elif level == 'moderate':
            interpretation = f"○ Moderate congruence ({score:.0%}) - Some mixed signals detected."
        else:
            interpretation = f"⚠ Low congruence ({score:.0%}) - Conflicting emotional signals."

        if alerts:
            alert_notes = [a['note'] for a in alerts[:2]]  # Top 2 alerts
            interpretation += f" Issues: {'; '.join(alert_notes)}"

        return interpretation
