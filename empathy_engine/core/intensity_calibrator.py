"""
EmpathyEngine - Emotion Intensity Calibrator
Measures emotion intensity on a 0-1 scale for granular emotional analysis

This module takes the detected emotion and calculates how INTENSE it is.
Example: "I'm happy" vs "I'M ABSOLUTELY ECSTATIC!!!" - both joy, different intensities.

Intensity factors:
- Sentiment magnitude (how far from neutral)
- Keyword strength (strong vs weak emotion words)
- Voice prosody features (energy, pitch variation)
- Textual indicators (caps, punctuation, intensifiers)
- Coherence across modalities

Created: December 18, 2025
Part of the "all of them" expansion
"""

import re
from typing import Dict, Optional, List
import numpy as np


class IntensityCalibrator:
    """
    Calibrates emotion intensity on a 0-1 scale.

    Intensity levels:
    - 0.0 - 0.3: Mild (subtle, barely noticeable)
    - 0.3 - 0.6: Moderate (clearly present, normal)
    - 0.6 - 1.0: Strong (intense, overwhelming)

    Usage:
        calibrator = IntensityCalibrator()
        intensity = calibrator.calibrate(analysis_result)
        # Returns: {'intensity': 0.75, 'level': 'strong', 'factors': {...}}
    """

    def __init__(self):
        # Emotion intensity modifiers (words that amplify/dampen emotions)
        self.intensifiers = {
            'extreme': ['extremely', 'incredibly', 'absolutely', 'totally', 'completely',
                       'utterly', 'deeply', 'profoundly', 'intensely', 'overwhelmingly',
                       'unbearably', 'devastatingly', 'monumentally'],
            'strong': ['very', 'really', 'so', 'quite', 'pretty', 'super', 'highly',
                      'seriously', 'truly', 'genuinely', 'definitely'],
            'moderate': ['somewhat', 'fairly', 'rather', 'kind of', 'sort of',
                        'relatively', 'moderately'],
            'mild': ['slightly', 'a bit', 'a little', 'barely', 'hardly',
                    'somewhat', 'mildly', 'faintly']
        }

        # Strong emotion keywords (indicate high intensity)
        self.strong_emotion_words = {
            'joy': ['ecstatic', 'thrilled', 'elated', 'overjoyed', 'euphoric', 'blissful'],
            'sadness': ['devastated', 'crushed', 'heartbroken', 'miserable', 'depressed', 'anguished'],
            'anger': ['furious', 'enraged', 'livid', 'irate', 'outraged', 'infuriated'],
            'fear': ['terrified', 'petrified', 'horrified', 'panic', 'dread', 'traumatized'],
            'anxiety': ['overwhelmed', 'panicked', 'consumed', 'paralyzed', 'crippled'],
            'disgust': ['revolted', 'sickened', 'repulsed', 'nauseated', 'appalled']
        }

        # Weak emotion keywords (indicate low intensity)
        self.weak_emotion_words = {
            'joy': ['content', 'pleased', 'glad', 'okay', 'fine', 'alright'],
            'sadness': ['down', 'blue', 'bummed', 'low', 'off', 'meh'],
            'anger': ['annoyed', 'irritated', 'bothered', 'miffed', 'peeved'],
            'fear': ['nervous', 'uneasy', 'worried', 'concerned', 'apprehensive'],
            'anxiety': ['worried', 'concerned', 'uneasy', 'tense', 'stressed'],
            'disgust': ['grossed out', 'put off', 'turned off', 'bothered']
        }

    def calibrate(self, analysis_result: Dict) -> Dict:
        """
        Calculate emotion intensity from analysis result.

        Args:
            analysis_result: Output from EmpathyEngine.analyze() or analyze_with_context()

        Returns:
            Dict with:
            - intensity: float 0-1 (overall intensity)
            - level: str ('mild', 'moderate', 'strong')
            - factors: Dict of contributing factors
            - confidence: float 0-1 (how confident we are in the intensity measurement)
        """
        text_analysis = analysis_result.get('text_analysis', {})
        voice_analysis = analysis_result.get('voice_analysis', {})
        emotion = analysis_result.get('primary_emotion', 'neutral')

        # Calculate intensity from multiple factors
        factors = {}

        # Factor 1: Sentiment magnitude (0-1)
        sentiment_compound = abs(text_analysis.get('sentiment_compound', 0))
        factors['sentiment_magnitude'] = min(sentiment_compound, 1.0)

        # Factor 2: Text intensity markers (0-1)
        text = text_analysis.get('text', '')
        factors['text_markers'] = self._analyze_text_intensity(text, emotion)

        # Factor 3: Voice prosody intensity (0-1)
        if voice_analysis:
            factors['voice_intensity'] = self._analyze_voice_intensity(voice_analysis)
        else:
            factors['voice_intensity'] = None

        # Factor 4: Emotion confidence (higher confidence = clearer intensity signal)
        emotion_confidence = analysis_result.get('confidence', 0.5)
        factors['emotion_confidence'] = emotion_confidence

        # Factor 5: Agreement boost (when voice/text agree, intensity is clearer)
        agreement = analysis_result.get('agreement')
        if agreement is not None:
            factors['agreement_boost'] = 0.1 if agreement else -0.1
        else:
            factors['agreement_boost'] = 0.0

        # Combine factors into overall intensity
        intensity = self._compute_intensity(factors)

        # Determine intensity level
        if intensity < 0.3:
            level = 'mild'
        elif intensity < 0.6:
            level = 'moderate'
        else:
            level = 'strong'

        # Calculate confidence in intensity measurement
        confidence = self._compute_confidence(factors)

        return {
            'intensity': round(intensity, 3),
            'level': level,
            'factors': factors,
            'confidence': round(confidence, 3)
        }

    def _analyze_text_intensity(self, text: str, emotion: str) -> float:
        """
        Analyze text for intensity markers.

        Returns float 0-1 based on:
        - Intensifier words
        - Strong emotion words
        - Capitalization
        - Punctuation (!!!, ???)
        - Repetition
        """
        if not text:
            return 0.5  # Default neutral

        text_lower = text.lower()
        score = 0.5  # Start neutral

        # Check for intensifiers
        for level, words in self.intensifiers.items():
            for word in words:
                if word in text_lower:
                    if level == 'extreme':
                        score += 0.15
                    elif level == 'strong':
                        score += 0.10
                    elif level == 'moderate':
                        score += 0.05
                    elif level == 'mild':
                        score -= 0.05

        # Check for strong emotion words
        if emotion in self.strong_emotion_words:
            for word in self.strong_emotion_words[emotion]:
                if word in text_lower:
                    score += 0.2
                    break

        # Check for weak emotion words
        if emotion in self.weak_emotion_words:
            for word in self.weak_emotion_words[emotion]:
                if word in text_lower:
                    score -= 0.1
                    break

        # Capitalization (SHOUTING = higher intensity)
        caps_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)
        if caps_ratio > 0.5:  # More than half caps
            score += 0.2
        elif caps_ratio > 0.3:
            score += 0.1

        # Exclamation marks
        exclamation_count = text.count('!')
        if exclamation_count >= 3:
            score += 0.15
        elif exclamation_count >= 2:
            score += 0.1
        elif exclamation_count >= 1:
            score += 0.05

        # Question marks (can indicate uncertainty/anxiety intensity)
        question_count = text.count('?')
        if question_count >= 3:
            score += 0.1
        elif question_count >= 2:
            score += 0.05

        # Repeated characters (sooooo = emphasis)
        repeated_chars = len(re.findall(r'(.)\1{2,}', text_lower))
        if repeated_chars > 0:
            score += min(repeated_chars * 0.05, 0.15)

        # Clamp to 0-1
        return max(0.0, min(1.0, score))

    def _analyze_voice_intensity(self, voice_analysis: Dict) -> float:
        """
        Analyze voice prosody for intensity markers.

        Returns float 0-1 based on:
        - Energy (loudness)
        - Pitch variation
        - Speech rate
        - Spectral features
        """
        features = voice_analysis.get('prosody_features', {})

        if not features:
            return 0.5  # Default neutral if no features

        score = 0.5  # Start neutral

        # Energy (loudness) - higher energy = higher intensity
        energy_mean = features.get('energy_mean', 0)
        if energy_mean > 0.7:
            score += 0.15
        elif energy_mean > 0.5:
            score += 0.1
        elif energy_mean < 0.3:
            score -= 0.1

        # Pitch variation - more variation can indicate stronger emotion
        pitch_std = features.get('pitch_std', 0)
        if pitch_std > 0.6:
            score += 0.15
        elif pitch_std > 0.4:
            score += 0.1

        # Speech rate (tempo) - faster can mean excited/anxious
        tempo = features.get('tempo', 120)
        if tempo > 150:  # Fast
            score += 0.1
        elif tempo < 90:  # Slow (can indicate sadness/lethargy)
            score += 0.05

        # Spectral centroid - brightness of voice
        spectral_centroid = features.get('spectral_centroid_mean', 0.5)
        if spectral_centroid > 0.7:  # Brighter = more energy
            score += 0.1

        # Clamp to 0-1
        return max(0.0, min(1.0, score))

    def _compute_intensity(self, factors: Dict) -> float:
        """
        Combine all factors into overall intensity score.

        Weighted average:
        - Sentiment magnitude: 25%
        - Text markers: 30%
        - Voice intensity: 25% (if available)
        - Emotion confidence: 10%
        - Agreement boost: 10%
        """
        weights = {
            'sentiment_magnitude': 0.25,
            'text_markers': 0.30,
            'voice_intensity': 0.25,
            'emotion_confidence': 0.10,
            'agreement_boost': 0.10
        }

        # If no voice, redistribute its weight to text
        if factors.get('voice_intensity') is None:
            weights['text_markers'] += 0.25
            weights['voice_intensity'] = 0.0

        intensity = 0.0

        intensity += factors.get('sentiment_magnitude', 0) * weights['sentiment_magnitude']
        intensity += factors.get('text_markers', 0.5) * weights['text_markers']

        if factors.get('voice_intensity') is not None:
            intensity += factors['voice_intensity'] * weights['voice_intensity']

        # Emotion confidence contributes to intensity clarity
        intensity += factors.get('emotion_confidence', 0.5) * weights['emotion_confidence']

        # Agreement boost
        intensity += factors.get('agreement_boost', 0.0) * weights['agreement_boost']

        # Clamp to 0-1
        return max(0.0, min(1.0, intensity))

    def _compute_confidence(self, factors: Dict) -> float:
        """
        Calculate confidence in the intensity measurement.

        Higher confidence when:
        - Multiple modalities available
        - High emotion confidence
        - Text has clear markers
        - Voice/text agree
        """
        confidence = 0.5  # Start neutral

        # More modalities = higher confidence
        modality_count = sum([
            factors.get('sentiment_magnitude', 0) > 0,
            factors.get('text_markers', 0) > 0,
            factors.get('voice_intensity') is not None
        ])
        confidence += modality_count * 0.1

        # High emotion confidence boosts intensity confidence
        emotion_conf = factors.get('emotion_confidence', 0.5)
        confidence += (emotion_conf - 0.5) * 0.3

        # Agreement boosts confidence
        if factors.get('agreement_boost', 0) > 0:
            confidence += 0.15

        # Clamp to 0-1
        return max(0.0, min(1.0, confidence))

    def get_intensity_description(self, intensity: float, emotion: str) -> str:
        """
        Generate human-readable description of intensity.

        Args:
            intensity: 0-1 intensity score
            emotion: Emotion name

        Returns:
            Description like "mildly happy" or "intensely anxious"
        """
        if intensity < 0.3:
            modifier = "mildly"
        elif intensity < 0.6:
            modifier = "moderately"
        else:
            modifier = "intensely"

        return f"{modifier} {emotion}"

    def calibrate_batch(self, analysis_results: List[Dict]) -> List[Dict]:
        """
        Calibrate intensity for multiple analysis results.

        Args:
            analysis_results: List of analysis result dicts

        Returns:
            List of intensity calibration results
        """
        return [self.calibrate(result) for result in analysis_results]
