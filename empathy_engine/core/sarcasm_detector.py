"""
EmpathyEngine - Sarcasm & Irony Detector
Detects when expressed emotion contradicts intended meaning

This module catches sarcasm/irony by looking for:
- Positive words with negative context
- Exaggerated language (hyperbole)
- Text/voice mismatch patterns
- Specific sarcasm markers ("oh great", "wonderful", "fantastic")

Example: "Oh great, another meeting" - positive word, negative intent

Created: December 18, 2025
Part of the "all of them" expansion
"""

import re
from typing import Dict, Optional, List, Tuple
from collections import Counter


class SarcasmDetector:
    """
    Detects sarcasm and irony in emotional expression.

    Sarcasm indicators:
    - Sentiment-emotion mismatch (positive words, negative emotion)
    - Common sarcasm phrases
    - Exaggerated language
    - Voice/text contradiction patterns
    - Contextual markers

    Usage:
        detector = SarcasmDetector()
        result = detector.detect(analysis_result)
        # Returns: {'sarcasm_detected': True, 'confidence': 0.78, 'indicators': [...]}
    """

    def __init__(self):
        # Common sarcastic phrases/openers
        self.sarcasm_phrases = [
            r'\boh great\b',
            r'\boh wonderful\b',
            r'\boh fantastic\b',
            r'\bjust perfect\b',
            r'\bhow lovely\b',
            r'\bwow thanks\b',
            r'\byeah right\b',
            r'\bsure thing\b',
            r'\bof course\b',  # Context-dependent
            r'\bobviously\b',   # Context-dependent
            r'\bclearly\b',     # Context-dependent
            r'\btotally\b',     # Context-dependent
            r'\boh joy\b',
            r'\bhow nice\b',
            r'\bjust what I needed\b',
            r'\bcouldn\'t be better\b',
            r'\bbest day ever\b',
            r'\bliving the dream\b'
        ]

        # Exaggeration markers (hyperbole often signals sarcasm)
        self.hyperbole_markers = [
            r'\balways\b',
            r'\bnever\b',
            r'\beveryone\b',
            r'\bno one\b',
            r'\beverything\b',
            r'\bnothing\b',
            r'\b(absolute|complete|total|utter)ly\b',
            r'\b(million|billion|thousand) times\b',
            r'\beverywhere\b',
            r'\banywhere\b'
        ]

        # Positive words often used sarcastically
        self.sarcastic_positives = [
            'great', 'wonderful', 'fantastic', 'perfect', 'lovely',
            'amazing', 'brilliant', 'super', 'awesome', 'excellent',
            'marvelous', 'fabulous', 'delightful', 'terrific'
        ]

        # Negative context words (when paired with positive words = sarcasm)
        self.negative_context = [
            'another', 'more', 'just', 'already', 'still', 'again',
            'now', 'really', 'exactly', 'totally', 'completely',
            'oh', 'wow', 'yeah', 'sure'
        ]

        # Ellipsis and other punctuation patterns that suggest sarcasm
        self.punctuation_patterns = [
            r'\.{3,}',  # Ellipsis (...)
            r'\.\.\.',
            r'(?:!\?|\?!)',  # Mixed punctuation (!?)
        ]

    def detect(self, analysis_result: Dict) -> Dict:
        """
        Detect sarcasm/irony in analysis result.

        Args:
            analysis_result: Output from EmpathyEngine.analyze()

        Returns:
            Dict with:
            - sarcasm_detected: bool
            - confidence: float 0-1
            - indicators: List of detected sarcasm indicators
            - interpretation: str (what we think they really mean)
        """
        text_analysis = analysis_result.get('text_analysis', {})
        voice_analysis = analysis_result.get('voice_analysis', {})
        text = text_analysis.get('text', '')

        if not text:
            return self._no_detection()

        indicators = []
        confidence_score = 0.0

        # Indicator 1: Sarcastic phrases
        phrase_matches = self._detect_sarcastic_phrases(text)
        if phrase_matches:
            indicators.extend(phrase_matches)
            confidence_score += 0.4  # Strong indicator

        # Indicator 2: Positive word + negative context
        context_mismatches = self._detect_context_mismatch(text)
        if context_mismatches:
            indicators.extend(context_mismatches)
            confidence_score += 0.3

        # Indicator 3: Sentiment-emotion mismatch
        sentiment_mismatch = self._detect_sentiment_mismatch(text_analysis)
        if sentiment_mismatch:
            indicators.append(sentiment_mismatch)
            confidence_score += 0.25

        # Indicator 4: Hyperbole/exaggeration
        hyperbole = self._detect_hyperbole(text)
        if hyperbole:
            indicators.append(hyperbole)
            confidence_score += 0.15

        # Indicator 5: Punctuation patterns
        punctuation = self._detect_sarcastic_punctuation(text)
        if punctuation:
            indicators.append(punctuation)
            confidence_score += 0.1

        # Indicator 6: Voice/text mismatch (if voice available)
        if voice_analysis:
            voice_mismatch = self._detect_voice_text_sarcasm(
                text_analysis,
                voice_analysis,
                analysis_result
            )
            if voice_mismatch:
                indicators.append(voice_mismatch)
                confidence_score += 0.3

        # Clamp confidence to 0-1
        confidence = min(1.0, confidence_score)

        # Determine if sarcasm detected (threshold: 0.4)
        sarcasm_detected = confidence >= 0.4

        # Generate interpretation if sarcasm detected
        interpretation = None
        if sarcasm_detected:
            interpretation = self._generate_interpretation(
                text_analysis,
                indicators,
                confidence
            )

        return {
            'sarcasm_detected': sarcasm_detected,
            'confidence': round(confidence, 3),
            'indicators': indicators,
            'interpretation': interpretation,
            'inverted_emotion': self._invert_emotion(analysis_result) if sarcasm_detected else None
        }

    def _detect_sarcastic_phrases(self, text: str) -> List[str]:
        """Detect common sarcastic phrases."""
        text_lower = text.lower()
        matches = []

        for pattern in self.sarcasm_phrases:
            if re.search(pattern, text_lower):
                phrase = re.search(pattern, text_lower).group()
                matches.append(f"Sarcastic phrase: '{phrase}'")

        return matches

    def _detect_context_mismatch(self, text: str) -> List[str]:
        """Detect positive words in negative context."""
        text_lower = text.lower()
        words = text_lower.split()
        matches = []

        for i, word in enumerate(words):
            # Check if word is a sarcastic positive
            if any(pos in word for pos in self.sarcastic_positives):
                # Check surrounding context
                context_start = max(0, i - 2)
                context_end = min(len(words), i + 1)
                context_words = words[context_start:context_end]

                # If negative context word nearby, likely sarcasm
                if any(neg in context_words for neg in self.negative_context):
                    phrase = ' '.join(context_words)
                    matches.append(f"Positive word in negative context: '{phrase}'")

        return matches

    def _detect_sentiment_mismatch(self, text_analysis: Dict) -> Optional[str]:
        """
        Detect when sentiment and emotion don't match.

        Example: Positive words (high sentiment) but detected anger emotion.
        """
        sentiment = text_analysis.get('sentiment_compound', 0)
        emotion = text_analysis.get('emotion_primary', 'neutral')
        emotion_confidence = text_analysis.get('emotion_confidence', 0)

        # Positive sentiment but negative emotion
        if sentiment > 0.3 and emotion in ['anger', 'sadness', 'disgust', 'fear'] and emotion_confidence > 0.6:
            return f"Sentiment-emotion mismatch: Positive words ({sentiment:.2f}) but {emotion} detected"

        # Negative sentiment but positive emotion (less common sarcasm, but possible)
        if sentiment < -0.3 and emotion in ['joy', 'surprise'] and emotion_confidence > 0.6:
            return f"Sentiment-emotion mismatch: Negative words ({sentiment:.2f}) but {emotion} detected"

        return None

    def _detect_hyperbole(self, text: str) -> Optional[str]:
        """Detect exaggeration/hyperbole."""
        text_lower = text.lower()
        matches = []

        for pattern in self.hyperbole_markers:
            if re.search(pattern, text_lower):
                match = re.search(pattern, text_lower).group()
                matches.append(match)

        if matches:
            return f"Hyperbole detected: {', '.join(matches[:3])}"  # Show first 3
        return None

    def _detect_sarcastic_punctuation(self, text: str) -> Optional[str]:
        """Detect punctuation patterns that suggest sarcasm."""
        matches = []

        for pattern in self.punctuation_patterns:
            if re.search(pattern, text):
                matches.append(pattern)

        if matches:
            return "Sarcastic punctuation pattern"
        return None

    def _detect_voice_text_sarcasm(
        self,
        text_analysis: Dict,
        voice_analysis: Dict,
        fusion_result: Dict
    ) -> Optional[str]:
        """
        Detect sarcasm via voice/text contradiction.

        Sarcasm often involves saying positive words in a flat/negative tone.
        """
        text_sentiment = text_analysis.get('sentiment_compound', 0)
        voice_emotion = voice_analysis.get('prosody_emotion', 'neutral')
        agreement = fusion_result.get('agreement', True)

        # Positive text + flat/negative voice = possible sarcasm
        if text_sentiment > 0.3 and not agreement:
            if voice_emotion in ['sad', 'frustrated', 'calm', 'neutral']:
                return f"Voice/text mismatch: Positive text but {voice_emotion} tone"

        # High energy voice + negative text can also be sarcastic anger
        if text_sentiment < -0.3 and voice_emotion in ['angry', 'excited']:
            return f"Voice/text mismatch: Negative text with {voice_emotion} tone"

        return None

    def _generate_interpretation(
        self,
        text_analysis: Dict,
        indicators: List[str],
        confidence: float
    ) -> str:
        """
        Generate human-readable interpretation of sarcasm.

        Example: "Likely expressing frustration/annoyance, not genuine positivity"
        """
        emotion = text_analysis.get('emotion_primary', 'neutral')
        sentiment = text_analysis.get('sentiment_compound', 0)

        # If positive sentiment but detected as sarcasm
        if sentiment > 0.3:
            if confidence > 0.7:
                return "Likely expressing frustration/annoyance, not genuine positivity"
            else:
                return "Possibly sarcastic - may be expressing mild frustration"

        # If negative sentiment with sarcasm markers
        if sentiment < -0.3:
            return "Sarcastic expression of genuine negative emotion"

        # Neutral sentiment with sarcasm
        return "Ironic/sarcastic tone detected - true emotion masked"

    def _invert_emotion(self, analysis_result: Dict) -> Optional[str]:
        """
        Invert detected emotion if sarcasm present.

        Example: Detected 'joy' → likely 'frustration'
        """
        emotion = analysis_result.get('primary_emotion', 'neutral')

        inversion_map = {
            'joy': 'frustration',
            'surprise': 'annoyance',
            'neutral': 'mild_frustration',
            # Negative emotions stay negative when sarcastic
            'sadness': 'sadness',
            'anger': 'anger',
            'fear': 'anxiety',
            'disgust': 'disgust'
        }

        return inversion_map.get(emotion, 'frustration')

    def _no_detection(self) -> Dict:
        """Return structure for no sarcasm detected."""
        return {
            'sarcasm_detected': False,
            'confidence': 0.0,
            'indicators': [],
            'interpretation': None,
            'inverted_emotion': None
        }

    def detect_batch(self, analysis_results: List[Dict]) -> List[Dict]:
        """
        Detect sarcasm in multiple analysis results.

        Args:
            analysis_results: List of analysis result dicts

        Returns:
            List of sarcasm detection results
        """
        return [self.detect(result) for result in analysis_results]

    def get_sarcasm_summary(self, detection_result: Dict) -> str:
        """
        Generate human-readable summary.

        Args:
            detection_result: Output from detect()

        Returns:
            Summary like "Sarcasm detected (78% confidence) - likely frustration"
        """
        if not detection_result['sarcasm_detected']:
            return "No sarcasm detected"

        confidence = detection_result['confidence']
        inverted = detection_result.get('inverted_emotion', 'unclear')

        return f"Sarcasm detected ({confidence:.0%} confidence) - likely {inverted}"
