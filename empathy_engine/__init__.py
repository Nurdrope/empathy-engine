"""
EmpathyEngine - Multi-Modal Emotional Intelligence System

A standalone AI engine for emotional analysis combining:
- Text sentiment & emotion detection
- Voice prosody analysis (pitch, energy, rhythm)
- Cross-modality fusion for holistic emotional understanding
- Pattern detection over time

Original: MoodRing (Nov 2025)
Extracted: EmpathyEngine (Dec 2025)
"""

__version__ = "1.0.1"
__author__ = "Nurdrope"

from .core.engine import EmpathyEngine
from .core.text_analyzer import TextAnalyzer
from .core.voice_analyzer import VoiceAnalyzer
from .core.pattern_detector import PatternDetector
from .core.fusion import EmotionFusion

__all__ = [
    'EmpathyEngine',
    'TextAnalyzer',
    'VoiceAnalyzer',
    'PatternDetector',
    'EmotionFusion',
]
