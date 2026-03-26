"""
EmpathyEngine - Text Analysis Module
Sentiment, emotion detection, and keyword extraction

Extracted from MoodRing (Nov 2025)
"""

import json
from typing import Dict, Optional
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import yake


class TextAnalyzer:
    """
    Analyzes text for emotional content using:
    - VADER: Fast sentiment analysis (positive/negative/neutral)
    - Transformers: Deep emotion detection (joy, sadness, anger, fear, surprise, disgust, neutral)
    - YAKE: Keyword/theme extraction
    """

    def __init__(self):
        # Initialize VADER sentiment analyzer
        self.sentiment_analyzer = SentimentIntensityAnalyzer()

        # Initialize YAKE keyword extractor
        self.keyword_extractor = yake.KeywordExtractor(
            lan="en",
            n=2,  # max ngram size
            dedupLim=0.5,  # More aggressive deduplication
            top=10,
            features=None
        )

        # Emotion classifier (lazy loaded)
        self._emotion_classifier = None

        # Quick emotion mapping from VADER for short texts
        self._quick_emotion_map = {
            'positive': {'joy': 0.7, 'neutral': 0.2, 'surprise': 0.1},
            'negative': {'sadness': 0.5, 'anger': 0.3, 'fear': 0.2},
            'neutral': {'neutral': 0.8, 'surprise': 0.1, 'joy': 0.1}
        }

    def _load_emotion_classifier(self):
        """Load emotion classifier (lazy loading for performance)."""
        if self._emotion_classifier is None:
            from transformers import pipeline
            self._emotion_classifier = pipeline(
                "text-classification",
                model="j-hartmann/emotion-english-distilroberta-base",
                top_k=None
            )
        return self._emotion_classifier

    def analyze_sentiment(self, text: str) -> Dict:
        """
        Analyze sentiment using VADER.

        Args:
            text: Input text to analyze

        Returns:
            Dict with sentiment_label, sentiment_positive, sentiment_negative,
            sentiment_neutral, sentiment_compound scores
        """
        scores = self.sentiment_analyzer.polarity_scores(text)

        # Determine overall label
        compound = scores['compound']
        if compound >= 0.05:
            label = 'positive'
        elif compound <= -0.05:
            label = 'negative'
        else:
            label = 'neutral'

        return {
            'sentiment_label': label,
            'sentiment_positive': scores['pos'],
            'sentiment_negative': scores['neg'],
            'sentiment_neutral': scores['neu'],
            'sentiment_compound': compound
        }

    def analyze_emotions(self, text: str) -> Dict:
        """
        Detect emotions using transformer model.

        Args:
            text: Input text to analyze

        Returns:
            Dict with emotion_primary, emotion_confidence, emotions_json
        """
        try:
            classifier = self._load_emotion_classifier()
            results = classifier(text[:512])[0]  # Limit text length

            # Sort by score
            sorted_emotions = sorted(results, key=lambda x: x['score'], reverse=True)
            primary = sorted_emotions[0]

            # Create emotions dict for storage
            emotions_dict = {e['label']: round(e['score'], 4) for e in sorted_emotions}

            return {
                'emotion_primary': primary['label'],
                'emotion_confidence': round(primary['score'], 4),
                'emotions_json': json.dumps(emotions_dict)
            }
        except Exception as e:
            print(f"Emotion analysis error: {e}")
            return {
                'emotion_primary': None,
                'emotion_confidence': None,
                'emotions_json': None
            }

    def extract_keywords(self, text: str) -> Dict:
        """
        Extract keywords/themes using YAKE.

        Args:
            text: Input text to analyze

        Returns:
            Dict with keywords_json (list of keywords as JSON string)
        """
        try:
            keywords = self.keyword_extractor.extract_keywords(text)
            # YAKE returns (keyword, score) tuples, lower score = more relevant
            keyword_list = [kw[0] for kw in keywords[:10]]

            # Manual deduplication: remove exact duplicates and lowercase variations
            seen = set()
            unique_keywords = []
            for kw in keyword_list:
                kw_lower = kw.lower()
                if kw_lower not in seen:
                    seen.add(kw_lower)
                    unique_keywords.append(kw)
                if len(unique_keywords) >= 5:  # Limit to top 5 unique keywords
                    break

            return {
                'keywords_json': json.dumps(unique_keywords)
            }
        except Exception as e:
            print(f"Keyword extraction error: {e}")
            return {
                'keywords_json': None
            }

    def analyze_quick(self, text: str) -> Dict:
        """
        Quick analysis for short texts using VADER-based emotion inference.
        Much faster than full transformer-based analysis.

        Args:
            text: Input text to analyze

        Returns:
            Dict with sentiment and quick emotion inference
        """
        if not text or not text.strip():
            return {}

        results = {}

        # Sentiment analysis (always fast)
        sentiment = self.analyze_sentiment(text)
        results.update(sentiment)

        # Quick emotion inference from sentiment
        sentiment_label = sentiment.get('sentiment_label', 'neutral')
        emotion_dist = self._quick_emotion_map.get(sentiment_label, self._quick_emotion_map['neutral'])

        # Get primary emotion
        primary_emotion = max(emotion_dist.items(), key=lambda x: x[1])
        results['emotion_primary'] = primary_emotion[0]
        results['emotion_confidence'] = primary_emotion[1]
        results['emotions_json'] = json.dumps(emotion_dist)

        # Skip keyword extraction for very short texts
        word_count = len(text.split())
        if word_count >= 5:
            keywords = self.extract_keywords(text)
            results.update(keywords)
        else:
            results['keywords_json'] = json.dumps([])

        return results

    def analyze(self, text: str, force_full: bool = False) -> Dict:
        """
        Perform analysis on text.
        Uses quick analysis for short texts (<20 words) unless force_full=True.

        Args:
            text: Input text to analyze
            force_full: Force full transformer analysis even for short text

        Returns:
            Combined dict with all analysis results
        """
        if not text or not text.strip():
            return {}

        word_count = len(text.split())

        # Use quick analysis for short entries
        if word_count < 20 and not force_full:
            return self.analyze_quick(text)

        results = {}

        # Sentiment analysis
        sentiment = self.analyze_sentiment(text)
        results.update(sentiment)

        # Emotion detection (full transformer model)
        emotions = self.analyze_emotions(text)
        results.update(emotions)

        # Keyword extraction
        keywords = self.extract_keywords(text)
        results.update(keywords)

        return results

    def is_negative_short(self, text: str) -> bool:
        """
        Check if text is a short negative entry that might need follow-up.

        Args:
            text: Input text to check

        Returns:
            True if entry is <15 words and negative sentiment
        """
        if not text or not text.strip():
            return False

        word_count = len(text.split())
        if word_count >= 15:
            return False

        scores = self.sentiment_analyzer.polarity_scores(text)
        return scores['compound'] <= -0.3

    def is_expressing_emotion(self, text: str) -> bool:
        """
        Check if user is expressing emotion (any emotion is positive engagement).
        Expression is always good - silence is the red flag.

        Args:
            text: Input text to check

        Returns:
            True if the text shows emotional content worth exploring further
        """
        if not text or not text.strip():
            return False

        word_count = len(text.split())

        # Short emotional entries are great opportunities to encourage more
        if word_count > 30:
            return False  # Long entries already express enough

        scores = self.sentiment_analyzer.polarity_scores(text)
        compound = abs(scores['compound'])

        # Any strong emotion (positive OR negative) means they're opening up
        return compound >= 0.3

    def is_avoidance(self, text: str) -> bool:
        """
        Detect avoidance patterns - these are the real red flags.
        Words like 'fine', 'ok', 'whatever' often mask real feelings.

        Args:
            text: Input text to check

        Returns:
            True if text shows avoidance patterns
        """
        if not text or not text.strip():
            return False

        text_lower = text.lower().strip()
        word_count = len(text.split())

        # Common avoidance words/phrases
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

        # Check for avoidance patterns in short responses
        if word_count <= 5:
            for pattern in avoidance_patterns:
                if text_lower == pattern or text_lower.startswith(pattern + '.') or text_lower.startswith(pattern + '!'):
                    return True

        # Also check sentiment - very neutral short responses
        if word_count <= 3:
            scores = self.sentiment_analyzer.polarity_scores(text)
            if abs(scores['compound']) < 0.1:
                return True

        return False

    def get_mood_summary(self, analysis: Dict) -> str:
        """
        Generate a human-readable mood summary from analysis results.

        Args:
            analysis: Analysis dict from analyze()

        Returns:
            Human-readable summary string
        """
        if not analysis:
            return "No analysis available"

        parts = []

        # Sentiment
        sentiment = analysis.get('sentiment_label', 'unknown')
        compound = analysis.get('sentiment_compound', 0)
        intensity = abs(compound)

        if intensity > 0.6:
            strength = "strongly"
        elif intensity > 0.3:
            strength = "moderately"
        else:
            strength = "slightly"

        if sentiment != 'neutral':
            parts.append(f"{strength} {sentiment}")
        else:
            parts.append("neutral")

        # Primary emotion
        emotion = analysis.get('emotion_primary')
        if emotion:
            confidence = analysis.get('emotion_confidence', 0)
            if confidence > 0.5:
                parts.append(f"feeling {emotion}")

        # Keywords
        keywords_json = analysis.get('keywords_json')
        if keywords_json:
            try:
                keywords = json.loads(keywords_json)
                if keywords:
                    parts.append(f"themes: {', '.join(keywords[:3])}")
            except:
                pass

        return " | ".join(parts)
