"""
EmpathyEngine - Multi-Modal Emotion Fusion
Cross-modality emotional intelligence combining text, voice, and behavioral patterns

This is the "secret sauce" - what made MoodRing catch fear at 95.9% confidence
and detect frustration beneath positive words.
"""

import json
from typing import Dict, Optional, List
import numpy as np


class EmotionFusion:
    """
    Fuses emotional signals from multiple modalities:
    - Text sentiment & emotion (what they said)
    - Voice prosody (how they said it)
    - Behavioral patterns (context over time)

    The magic: Voice can contradict text. Someone saying "I'm fine" with
    frustrated prosody triggers a higher-confidence frustration detection.
    This is how we "see through lies" and catch authentic emotional states.
    """

    # Emotion mapping for cross-modality fusion
    EMOTION_COMPATIBILITY = {
        # Text emotions -> Compatible voice prosody
        'joy': ['excited', 'elevated', 'calm'],
        'sadness': ['sad', 'calm', 'neutral'],
        'anger': ['angry', 'frustrated', 'elevated'],
        'fear': ['frustrated', 'elevated', 'neutral'],
        'surprise': ['excited', 'elevated'],
        'disgust': ['frustrated', 'angry'],
        'neutral': ['neutral', 'calm'],

        # Voice prosody -> Compatible text emotions
        'calm': ['neutral', 'joy', 'sadness'],
        'sad': ['sadness', 'neutral'],
        'frustrated': ['anger', 'fear', 'disgust'],
        'elevated': ['joy', 'surprise', 'fear'],
        'angry': ['anger', 'disgust'],
        'excited': ['joy', 'surprise'],
    }

    def __init__(self):
        pass

    def fuse(
        self,
        text_analysis: Optional[Dict] = None,
        voice_analysis: Optional[Dict] = None,
        historical_context: Optional[Dict] = None
    ) -> Dict:
        """
        Fuse multi-modal emotional signals into unified assessment.

        Args:
            text_analysis: Output from TextAnalyzer.analyze()
            voice_analysis: Output from VoiceAnalyzer.analyze()
            historical_context: Optional context from PatternDetector

        Returns:
            Dict with:
            - primary_emotion: Final fused emotion
            - confidence: 0-1 confidence score
            - modalities: Which signals contributed
            - agreement: Whether text and voice agree
            - authenticity_score: How "real" the emotion seems (0-1)
            - fusion_notes: Human-readable explanation
        """
        if not text_analysis and not voice_analysis:
            return {
                'primary_emotion': 'neutral',
                'confidence': 0.0,
                'modalities': [],
                'agreement': None,
                'authenticity_score': 0.0,
                'fusion_notes': 'No data available'
            }

        modalities = []
        signals = []

        # Extract text emotion signal
        text_emotion = None
        text_confidence = 0.0
        if text_analysis:
            text_emotion = text_analysis.get('emotion_primary')
            text_confidence = text_analysis.get('emotion_confidence', 0.0)
            if text_emotion:
                signals.append({
                    'modality': 'text',
                    'emotion': text_emotion,
                    'confidence': text_confidence,
                    'weight': 0.5  # Base weight
                })
                modalities.append('text')

        # Extract voice emotion signal
        voice_emotion = None
        voice_confidence = 0.0
        if voice_analysis:
            voice_emotion = voice_analysis.get('prosody_emotion')
            voice_confidence = voice_analysis.get('prosody_confidence', 0.0)
            if voice_emotion:
                signals.append({
                    'modality': 'voice',
                    'emotion': voice_emotion,
                    'confidence': voice_confidence,
                    'weight': 0.6  # Voice often more reliable than words
                })
                modalities.append('voice')

        # Check cross-modality agreement
        agreement = None
        authenticity_boost = 0.0

        if text_emotion and voice_emotion:
            compatible = self._check_compatibility(text_emotion, voice_emotion)
            agreement = compatible

            if compatible:
                # Emotions agree = high authenticity
                authenticity_boost = 0.3
                # Boost confidence of both signals
                for signal in signals:
                    signal['weight'] *= 1.2
            else:
                # Emotions disagree = voice is probably more authentic
                # THIS is the breakthrough moment - catching "I'm fine" when frustrated
                for signal in signals:
                    if signal['modality'] == 'voice':
                        signal['weight'] *= 1.5  # Trust voice over text
                        authenticity_boost = 0.2  # Still authentic, just hidden
                    else:
                        signal['weight'] *= 0.7  # Discount contradicting text

        # Weighted emotion voting
        emotion_scores = {}
        for signal in signals:
            emotion = signal['emotion']
            weighted_confidence = signal['confidence'] * signal['weight']

            if emotion not in emotion_scores:
                emotion_scores[emotion] = 0.0
            emotion_scores[emotion] += weighted_confidence

        # Get primary emotion
        if emotion_scores:
            primary_emotion = max(emotion_scores.items(), key=lambda x: x[1])
            final_emotion = primary_emotion[0]
            final_confidence = min(primary_emotion[1], 1.0)  # Cap at 1.0
        else:
            final_emotion = 'neutral'
            final_confidence = 0.0

        # Calculate authenticity score
        base_authenticity = np.mean([s['confidence'] for s in signals]) if signals else 0.0
        authenticity_score = min(base_authenticity + authenticity_boost, 1.0)

        # Generate fusion notes
        fusion_notes = self._generate_fusion_notes(
            text_emotion, text_confidence,
            voice_emotion, voice_confidence,
            agreement, final_emotion, final_confidence
        )

        return {
            'primary_emotion': final_emotion,
            'confidence': round(final_confidence, 4),
            'modalities': modalities,
            'agreement': agreement,
            'authenticity_score': round(authenticity_score, 4),
            'fusion_notes': fusion_notes,
            'signals': signals,  # Debug info
            'text_emotion': text_emotion,
            'voice_emotion': voice_emotion
        }

    def _check_compatibility(self, text_emotion: str, voice_emotion: str) -> bool:
        """
        Check if text and voice emotions are compatible.

        Args:
            text_emotion: Emotion from text
            voice_emotion: Emotion from voice

        Returns:
            True if compatible, False if contradictory
        """
        # Check if voice emotion is compatible with text emotion
        text_compatible = self.EMOTION_COMPATIBILITY.get(text_emotion, [])
        voice_compatible = self.EMOTION_COMPATIBILITY.get(voice_emotion, [])

        return (voice_emotion in text_compatible) or (text_emotion in voice_compatible)

    def _generate_fusion_notes(
        self,
        text_emotion: Optional[str],
        text_confidence: float,
        voice_emotion: Optional[str],
        voice_confidence: float,
        agreement: Optional[bool],
        final_emotion: str,
        final_confidence: float
    ) -> str:
        """Generate human-readable fusion explanation."""

        if not text_emotion and not voice_emotion:
            return "No emotional signals detected."

        notes = []

        # Single modality
        if text_emotion and not voice_emotion:
            return f"Text analysis: {text_emotion} ({text_confidence:.1%} confidence)"

        if voice_emotion and not text_emotion:
            return f"Voice analysis: {voice_emotion} ({voice_confidence:.1%} confidence)"

        # Multi-modal fusion
        if agreement is True:
            notes.append(
                f"Text and voice agree: {text_emotion} (text) + {voice_emotion} (voice) = {final_emotion} "
                f"({final_confidence:.1%} confidence, high authenticity)"
            )
        elif agreement is False:
            notes.append(
                f"Text/voice mismatch detected: '{text_emotion}' (text) vs '{voice_emotion}' (voice). "
                f"Voice tone suggests true emotion: {final_emotion} ({final_confidence:.1%} confidence). "
                f"Possible emotional masking."
            )
        else:
            notes.append(
                f"Fused emotion: {final_emotion} ({final_confidence:.1%} confidence)"
            )

        return " ".join(notes)

    def enhance_with_context(
        self,
        fusion_result: Dict,
        historical_patterns: Optional[Dict] = None
    ) -> Dict:
        """
        Enhance fusion result with historical context/patterns.

        Args:
            fusion_result: Output from fuse()
            historical_patterns: Output from PatternDetector.detect_all_patterns()

        Returns:
            Enhanced fusion dict with contextual insights
        """
        if not historical_patterns:
            return fusion_result

        context_notes = []

        # Check for anxiety patterns
        anxiety = historical_patterns.get('anxiety_spikes', {})
        if anxiety.get('detected') and fusion_result['primary_emotion'] in ['fear', 'anxiety']:
            context_notes.append(
                f"Part of detected anxiety pattern ({anxiety.get('spike_count')} recent spikes)"
            )

        # Check for low energy patterns
        low_energy = historical_patterns.get('low_energy', {})
        if low_energy.get('detected') and fusion_result['primary_emotion'] in ['sadness']:
            context_notes.append(
                f"Consistent with low-energy period ({low_energy.get('period_count')} periods detected)"
            )

        # Check for mood volatility
        swings = historical_patterns.get('mood_swings', {})
        if swings.get('detected') and swings.get('volatility', 0) > 0.5:
            context_notes.append(
                f"High mood volatility detected (volatility: {swings.get('volatility')})"
            )

        if context_notes:
            fusion_result['context_notes'] = " | ".join(context_notes)
            fusion_result['contextual_confidence'] = min(
                fusion_result['confidence'] * 1.1,  # Slight boost from pattern confirmation
                1.0
            )

        return fusion_result
