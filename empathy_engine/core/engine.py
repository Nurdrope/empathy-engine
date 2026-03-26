"""
EmpathyEngine - Main Engine Interface
Unified interface for multi-modal emotional intelligence

This is the high-level API that brings it all together.
"""

from typing import Dict, Optional, List
from .text_analyzer import TextAnalyzer
from .voice_analyzer import VoiceAnalyzer
from .pattern_detector import PatternDetector
from .fusion import EmotionFusion
from .summaries import SummaryGenerator

# Advanced modules (December 2025 expansion)
from .intensity_calibrator import IntensityCalibrator
from .sarcasm_detector import SarcasmDetector
from .crisis_detector import CrisisDetector
from .baseline_profiler import BaselineProfiler
from .transition_tracker import TransitionTracker
from .contextual_modifier import ContextualModifier
from .congruence_checker import CongruenceChecker
from .emotion_predictor import EmotionPredictor
from .trigger_identifier import TriggerIdentifier
from .group_analyzer import GroupEmotionAnalyzer
from .cultural_adapter import CulturalAdapter
from .coherence_scorer import CoherenceScorer


class EmpathyEngine:
    """
    Main engine for multi-modal emotional analysis.

    The EmpathyEngine combines:
    1. Text analysis (VADER + Transformers)
    2. Voice prosody analysis (librosa)
    3. Pattern detection (temporal analysis)
    4. Cross-modality fusion (the secret sauce)

    Usage:
        # Initialize engine
        engine = EmpathyEngine()

        # Analyze text only
        result = engine.analyze_text("I'm feeling stressed")

        # Analyze voice only
        result = engine.analyze_voice("recording.wav")

        # Analyze both (full fusion)
        result = engine.analyze(
            text="I'm fine",
            audio_path="recording.wav"
        )

        # Add historical context
        result_with_context = engine.analyze_with_context(
            text="I'm worried again",
            entries=historical_entries
        )
    """

    def __init__(self):
        """Initialize all sub-analyzers."""
        # Core analyzers
        self.text_analyzer = TextAnalyzer()
        self.voice_analyzer = VoiceAnalyzer()
        self.pattern_detector = PatternDetector()
        self.fusion = EmotionFusion()
        self.summaries = SummaryGenerator()

        # Advanced modules (lazy-loaded on first use for performance)
        self._intensity_calibrator = None
        self._sarcasm_detector = None
        self._crisis_detector = None
        self._baseline_profiler = None
        self._transition_tracker = None
        self._contextual_modifier = None
        self._congruence_checker = None
        self._emotion_predictor = None
        self._trigger_identifier = None
        self._group_analyzer = None
        self._cultural_adapter = None
        self._coherence_scorer = None

    # Lazy loading properties for advanced modules
    @property
    def intensity_calibrator(self):
        if self._intensity_calibrator is None:
            self._intensity_calibrator = IntensityCalibrator()
        return self._intensity_calibrator

    @property
    def sarcasm_detector(self):
        if self._sarcasm_detector is None:
            self._sarcasm_detector = SarcasmDetector()
        return self._sarcasm_detector

    @property
    def crisis_detector(self):
        if self._crisis_detector is None:
            self._crisis_detector = CrisisDetector()
        return self._crisis_detector

    @property
    def baseline_profiler(self):
        if self._baseline_profiler is None:
            self._baseline_profiler = BaselineProfiler()
        return self._baseline_profiler

    @property
    def transition_tracker(self):
        if self._transition_tracker is None:
            self._transition_tracker = TransitionTracker()
        return self._transition_tracker

    @property
    def contextual_modifier(self):
        if self._contextual_modifier is None:
            self._contextual_modifier = ContextualModifier()
        return self._contextual_modifier

    @property
    def congruence_checker(self):
        if self._congruence_checker is None:
            self._congruence_checker = CongruenceChecker()
        return self._congruence_checker

    @property
    def emotion_predictor(self):
        if self._emotion_predictor is None:
            self._emotion_predictor = EmotionPredictor()
        return self._emotion_predictor

    @property
    def trigger_identifier(self):
        if self._trigger_identifier is None:
            self._trigger_identifier = TriggerIdentifier()
        return self._trigger_identifier

    @property
    def group_analyzer(self):
        if self._group_analyzer is None:
            self._group_analyzer = GroupEmotionAnalyzer()
        return self._group_analyzer

    @property
    def cultural_adapter(self):
        if self._cultural_adapter is None:
            self._cultural_adapter = CulturalAdapter()
        return self._cultural_adapter

    @property
    def coherence_scorer(self):
        if self._coherence_scorer is None:
            self._coherence_scorer = CoherenceScorer()
        return self._coherence_scorer

    def analyze_text(self, text: str, force_full: bool = False) -> Dict:
        """
        Analyze text for emotional content.

        Args:
            text: Input text to analyze
            force_full: Force full transformer analysis

        Returns:
            Dict with sentiment, emotion, keywords
        """
        return self.text_analyzer.analyze(text, force_full=force_full)

    def analyze_voice(self, audio_path: str) -> Dict:
        """
        Analyze voice prosody for emotional content.

        Args:
            audio_path: Path to audio file (WAV)

        Returns:
            Dict with prosody emotion, confidence, features
        """
        return self.voice_analyzer.analyze(audio_path)

    def analyze(
        self,
        text: Optional[str] = None,
        audio_path: Optional[str] = None,
        force_full_text: bool = False
    ) -> Dict:
        """
        Full multi-modal analysis with fusion.

        Args:
            text: Optional text to analyze
            audio_path: Optional audio file to analyze
            force_full_text: Force full transformer text analysis

        Returns:
            Dict with fused emotional assessment
        """
        text_analysis = None
        voice_analysis = None

        if text:
            text_analysis = self.text_analyzer.analyze(text, force_full=force_full_text)

        if audio_path:
            voice_analysis = self.voice_analyzer.analyze(audio_path)

        # Fuse modalities
        fusion_result = self.fusion.fuse(
            text_analysis=text_analysis,
            voice_analysis=voice_analysis
        )

        # Include raw analysis in result
        fusion_result['text_analysis'] = text_analysis
        fusion_result['voice_analysis'] = voice_analysis

        return fusion_result

    def analyze_with_context(
        self,
        text: Optional[str] = None,
        audio_path: Optional[str] = None,
        entries: Optional[List[Dict]] = None,
        pattern_days: int = 30,
        force_full_text: bool = False
    ) -> Dict:
        """
        Full analysis with historical context and pattern detection.

        Args:
            text: Optional text to analyze
            audio_path: Optional audio file to analyze
            entries: Historical entries for pattern detection
            pattern_days: Number of days to analyze for patterns
            force_full_text: Force full transformer text analysis

        Returns:
            Dict with fused emotional assessment + contextual insights
        """
        # Perform multi-modal analysis
        fusion_result = self.analyze(
            text=text,
            audio_path=audio_path,
            force_full_text=force_full_text
        )

        # Add pattern detection if historical data provided
        if entries:
            self.pattern_detector.set_entries(entries)
            patterns = self.pattern_detector.detect_all_patterns(days=pattern_days)

            # Enhance fusion with context
            fusion_result = self.fusion.enhance_with_context(
                fusion_result,
                historical_patterns=patterns
            )

            fusion_result['patterns'] = patterns

        return fusion_result

    def detect_patterns(
        self,
        entries: List[Dict],
        days: int = 30
    ) -> Dict:
        """
        Detect emotional patterns from historical data.

        Args:
            entries: List of historical entries
            days: Number of days to analyze

        Returns:
            Dict with detected patterns
        """
        self.pattern_detector.set_entries(entries)
        return self.pattern_detector.detect_all_patterns(days=days)

    def batch_analyze(
        self,
        items: List[Dict],
        include_patterns: bool = False
    ) -> List[Dict]:
        """
        Batch analyze multiple items.

        Args:
            items: List of dicts with 'text' and/or 'audio_path' keys
            include_patterns: Include pattern detection across all items

        Returns:
            List of analysis results
        """
        results = []

        for item in items:
            result = self.analyze(
                text=item.get('text'),
                audio_path=item.get('audio_path')
            )
            results.append(result)

        # Add pattern detection if requested
        if include_patterns and results:
            # Convert results to entries format
            entries = []
            for i, result in enumerate(results):
                entry = {
                    'timestamp': items[i].get('timestamp', ''),
                    'text': items[i].get('text', ''),
                    'emotion_primary': result.get('primary_emotion'),
                    'sentiment_compound': result.get('text_analysis', {}).get('sentiment_compound', 0),
                    'keywords_json': result.get('text_analysis', {}).get('keywords_json'),
                }
                if result.get('voice_analysis'):
                    entry['prosody_emotion'] = result['voice_analysis'].get('prosody_emotion')
                entries.append(entry)

            patterns = self.detect_patterns(entries)

            # Add patterns to each result
            for result in results:
                result['patterns'] = patterns

        return results

    def get_mood_summary(self, analysis_result: Dict) -> str:
        """
        Generate human-readable summary from analysis result.

        Args:
            analysis_result: Output from analyze() or analyze_with_context()

        Returns:
            Human-readable summary string
        """
        parts = []

        # Primary emotion
        emotion = analysis_result.get('primary_emotion')
        confidence = analysis_result.get('confidence', 0)
        parts.append(f"{emotion} ({confidence:.1%} confidence)")

        # Modalities
        modalities = analysis_result.get('modalities', [])
        if modalities:
            parts.append(f"Sources: {', '.join(modalities)}")

        # Agreement
        agreement = analysis_result.get('agreement')
        if agreement is not None:
            if agreement:
                parts.append("text/voice agree")
            else:
                parts.append("text/voice mismatch detected")

        # Authenticity
        authenticity = analysis_result.get('authenticity_score', 0)
        if authenticity > 0.7:
            parts.append(f"high authenticity ({authenticity:.1%})")
        elif authenticity > 0.4:
            parts.append(f"moderate authenticity ({authenticity:.1%})")

        return " | ".join(parts)

    def generate_summary(
        self,
        entries: List[Dict],
        period: str = 'daily',
        date: Optional[object] = None
    ) -> Dict:
        """
        Generate emotional summary for a time period.

        Args:
            entries: List of historical entries (each with timestamp, emotion, sentiment, keywords)
            period: 'daily', 'weekly', or 'monthly'
            date: Target date (datetime object or None for today/current)

        Returns:
            Dict with summary statistics, mood trends, and narrative

        Example:
            # Daily summary
            summary = engine.generate_summary(entries, period='daily')

            # Weekly summary
            summary = engine.generate_summary(entries, period='weekly')

            # Monthly summary (specific month)
            from datetime import datetime
            summary = engine.generate_summary(
                entries,
                period='monthly',
                date=datetime(2025, 11, 1)
            )
        """
        if period == 'daily':
            return self.summaries.generate_daily(entries, date)
        elif period == 'weekly':
            return self.summaries.generate_weekly(entries, date)
        elif period == 'monthly':
            # For monthly, date should be a datetime with year/month
            if date:
                return self.summaries.generate_monthly(entries, date.year, date.month)
            return self.summaries.generate_monthly(entries)
        else:
            raise ValueError(f"Invalid period: {period}. Must be 'daily', 'weekly', or 'monthly'")
