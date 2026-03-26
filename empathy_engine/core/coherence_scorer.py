"""
EmpathyEngine - Emotional Coherence Scorer
Scores overall quality and reliability of emotional analysis

This module provides a final quality score for the analysis by evaluating:
- Data completeness (how much information is available)
- Signal strength (how clear the emotional signals are)
- Multi-modal agreement (if text/voice align)
- Temporal consistency (does this fit with history)
- Contextual fit (does emotion make sense given situation)

Coherence score (0-1):
- 0.9-1.0: Excellent - highly reliable analysis
- 0.7-0.9: Good - reliable with minor gaps
- 0.5-0.7: Moderate - usable but some uncertainty
- 0.3-0.5: Low - significant uncertainty
- 0.0-0.3: Poor - unreliable, insufficient data

Created: December 18, 2025
Part of the "all of them" expansion - THE FINAL MODULE!
"""

from typing import Dict, Optional, List
import numpy as np


class CoherenceScorer:
    """
    Scores the overall coherence and reliability of emotional analysis.

    This is the "meta-analyzer" - it evaluates the quality of the analysis itself.

    Coherence dimensions:
    1. Data completeness: How much data is available
    2. Signal strength: How clear/confident the signals are
    3. Multi-modal agreement: Voice/text alignment
    4. Congruence: Internal consistency
    5. Contextual fit: Makes sense given situation
    6. Historical consistency: Fits with user's patterns

    Usage:
        scorer = CoherenceScorer()

        # Score a complete analysis
        coherence = scorer.score_coherence(
            analysis_result,
            intensity_result=intensity,
            sarcasm_result=sarcasm,
            congruence_result=congruence,
            context_result=context,
            baseline_deviation=baseline_dev
        )
        # Returns: {'score': 0.85, 'level': 'good', 'strengths': [...], 'weaknesses': [...]}
    """

    def __init__(self):
        pass

    def score_coherence(
        self,
        analysis_result: Dict,
        intensity_result: Optional[Dict] = None,
        sarcasm_result: Optional[Dict] = None,
        congruence_result: Optional[Dict] = None,
        context_result: Optional[Dict] = None,
        baseline_deviation: Optional[Dict] = None,
        cultural_adaptation: Optional[Dict] = None
    ) -> Dict:
        """
        Score overall coherence and reliability of analysis.

        Args:
            analysis_result: Base analysis from EmpathyEngine
            intensity_result: Output from IntensityCalibrator
            sarcasm_result: Output from SarcasmDetector
            congruence_result: Output from CongruenceChecker
            context_result: Output from ContextualModifier
            baseline_deviation: Output from BaselineProfiler
            cultural_adaptation: Output from CulturalAdapter

        Returns:
            Dict with:
            - score: Overall coherence score 0-1
            - level: Quality level (excellent/good/moderate/low/poor)
            - dimension_scores: Breakdown by dimension
            - strengths: What makes this analysis strong
            - weaknesses: What makes this analysis weak
            - reliability: Expected reliability percentage
            - recommendation: Should this analysis be trusted?
        """
        dimension_scores = {}
        strengths = []
        weaknesses = []

        # Dimension 1: Data Completeness (0-1)
        completeness = self._score_completeness(
            analysis_result,
            intensity_result,
            sarcasm_result,
            congruence_result,
            context_result
        )
        dimension_scores['completeness'] = completeness['score']
        if completeness['score'] >= 0.7:
            strengths.append(completeness['note'])
        else:
            weaknesses.append(completeness['note'])

        # Dimension 2: Signal Strength (0-1)
        signal_strength = self._score_signal_strength(analysis_result, intensity_result)
        dimension_scores['signal_strength'] = signal_strength['score']
        if signal_strength['score'] >= 0.7:
            strengths.append(signal_strength['note'])
        else:
            weaknesses.append(signal_strength['note'])

        # Dimension 3: Multi-modal Agreement (0-1, N/A if no voice)
        if analysis_result.get('voice_analysis'):
            agreement = self._score_agreement(analysis_result)
            dimension_scores['multi_modal_agreement'] = agreement['score']
            if agreement['score'] >= 0.7:
                strengths.append(agreement['note'])
            else:
                weaknesses.append(agreement['note'])

        # Dimension 4: Internal Congruence (0-1)
        if congruence_result:
            internal_congruence = congruence_result.get('score', 0.5)
            dimension_scores['internal_congruence'] = internal_congruence
            if internal_congruence >= 0.7:
                strengths.append(f"High internal congruence ({internal_congruence:.0%})")
            else:
                weaknesses.append(f"Low internal congruence ({internal_congruence:.0%})")

        # Dimension 5: Contextual Fit (0-1)
        if context_result:
            contextual_fit = self._score_contextual_fit(context_result)
            dimension_scores['contextual_fit'] = contextual_fit['score']
            if contextual_fit['score'] >= 0.7:
                strengths.append(contextual_fit['note'])
            else:
                weaknesses.append(contextual_fit['note'])

        # Dimension 6: Historical Consistency (0-1)
        if baseline_deviation:
            historical = self._score_historical_consistency(baseline_deviation)
            dimension_scores['historical_consistency'] = historical['score']
            if historical['score'] >= 0.7:
                strengths.append(historical['note'])
            else:
                weaknesses.append(historical['note'])

        # Penalty factors (reduce score if detected)
        penalties = 0.0

        # Sarcasm detected = less reliable
        if sarcasm_result and sarcasm_result.get('sarcasm_detected'):
            penalties += 0.1
            weaknesses.append(f"Sarcasm detected - stated emotion may be inverted")

        # Cultural adaptation needed = some uncertainty
        if cultural_adaptation and len(cultural_adaptation.get('cultural_notes', [])) > 0:
            penalties += 0.05
            weaknesses.append("Cultural adaptation applied - interpretation adjusted")

        # Calculate overall score
        if dimension_scores:
            base_score = np.mean(list(dimension_scores.values()))
            overall_score = max(0.0, base_score - penalties)
        else:
            overall_score = 0.3  # Default low if no dimensions

        # Determine quality level
        if overall_score >= 0.9:
            level = 'excellent'
            reliability = '90-95%'
            recommendation = 'Highly reliable - trust this analysis'
        elif overall_score >= 0.7:
            level = 'good'
            reliability = '70-90%'
            recommendation = 'Reliable - minor uncertainties but trustworthy'
        elif overall_score >= 0.5:
            level = 'moderate'
            reliability = '50-70%'
            recommendation = 'Usable with caution - some gaps in data'
        elif overall_score >= 0.3:
            level = 'low'
            reliability = '30-50%'
            recommendation = 'Uncertain - interpret carefully'
        else:
            level = 'poor'
            reliability = '< 30%'
            recommendation = 'Unreliable - insufficient data or conflicting signals'

        return {
            'score': round(overall_score, 3),
            'level': level,
            'dimension_scores': {k: round(v, 3) for k, v in dimension_scores.items()},
            'strengths': strengths,
            'weaknesses': weaknesses,
            'reliability': reliability,
            'recommendation': recommendation,
            'interpretation': self._generate_interpretation(overall_score, level, strengths, weaknesses)
        }

    def _score_completeness(
        self,
        analysis: Dict,
        intensity: Optional[Dict],
        sarcasm: Optional[Dict],
        congruence: Optional[Dict],
        context: Optional[Dict]
    ) -> Dict:
        """Score data completeness."""
        components = {
            'text_analysis': bool(analysis.get('text_analysis')),
            'voice_analysis': bool(analysis.get('voice_analysis')),
            'intensity': intensity is not None,
            'sarcasm_check': sarcasm is not None,
            'congruence_check': congruence is not None,
            'context': context is not None
        }

        available = sum(components.values())
        total = len(components)

        score = available / total

        return {
            'score': score,
            'note': f"{available}/{total} analysis components available"
        }

    def _score_signal_strength(self, analysis: Dict, intensity: Optional[Dict]) -> Dict:
        """Score how clear/confident the emotional signals are."""
        # Base confidence from emotion detection
        emotion_confidence = analysis.get('confidence', 0.5)

        # Sentiment magnitude (stronger sentiment = clearer signal)
        sentiment = abs(analysis.get('text_analysis', {}).get('sentiment_compound', 0))

        # Intensity confidence (if available)
        intensity_confidence = intensity.get('confidence', 0.5) if intensity else 0.5

        # Average all signal strengths
        signals = [emotion_confidence, sentiment, intensity_confidence]
        avg_strength = np.mean(signals)

        if avg_strength >= 0.7:
            note = f"Strong emotional signals (confidence: {avg_strength:.0%})"
        elif avg_strength >= 0.5:
            note = f"Moderate signal strength (confidence: {avg_strength:.0%})"
        else:
            note = f"Weak emotional signals (confidence: {avg_strength:.0%})"

        return {
            'score': avg_strength,
            'note': note
        }

    def _score_agreement(self, analysis: Dict) -> Dict:
        """Score multi-modal agreement."""
        agreement = analysis.get('agreement')
        authenticity = analysis.get('authenticity_score', 0.5)

        if agreement is None:
            return {'score': 0.5, 'note': 'No voice data for agreement check'}

        if agreement:
            return {
                'score': authenticity,
                'note': f"Voice/text agree (authenticity: {authenticity:.0%})"
            }
        else:
            return {
                'score': 0.4,  # Disagreement lowers score
                'note': f"Voice/text disagree - possible emotional masking"
            }

    def _score_contextual_fit(self, context_result: Dict) -> Dict:
        """Score how well emotion fits detected context."""
        contexts = context_result.get('context_detected', [])
        modifications = context_result.get('modifications', [])

        if not contexts:
            return {
                'score': 0.5,
                'note': 'No context detected to validate against'
            }

        # If context provides clarification, score higher
        if modifications:
            return {
                'score': 0.8,
                'note': f"Context provides clarity ({len(modifications)} contextual insights)"
            }
        else:
            return {
                'score': 0.6,
                'note': f"Context detected but minimal impact"
            }

    def _score_historical_consistency(self, baseline_deviation: Dict) -> Dict:
        """Score consistency with historical patterns."""
        is_deviation = baseline_deviation.get('is_deviation', False)
        severity = baseline_deviation.get('severity', 0)

        if not is_deviation:
            return {
                'score': 0.9,
                'note': 'Consistent with emotional baseline'
            }
        else:
            # Deviation is expected sometimes, but severe deviation lowers confidence
            if severity > 0.7:
                return {
                    'score': 0.5,
                    'note': f'Significant deviation from baseline ({severity:.0%})'
                }
            else:
                return {
                    'score': 0.7,
                    'note': f'Moderate deviation from baseline ({severity:.0%})'
                }

    def _generate_interpretation(
        self,
        score: float,
        level: str,
        strengths: List[str],
        weaknesses: List[str]
    ) -> str:
        """Generate human-readable interpretation."""
        parts = [f"Coherence: {level.upper()} ({score:.0%})"]

        if strengths:
            parts.append(f"Strengths: {', '.join(strengths[:2])}")

        if weaknesses:
            parts.append(f"Limitations: {', '.join(weaknesses[:2])}")

        return " | ".join(parts)
