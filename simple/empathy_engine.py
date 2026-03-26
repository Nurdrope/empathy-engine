"""
EMPATHY ENGINE - Simple Version
Detects true emotions by analyzing text + voice together
"""

from text_analysis import TextAnalyzer
from voice_analysis import VoiceAnalyzer
from fusion import EmotionFusion


class EmpathyEngine:
    """
    Simple emotional intelligence engine.

    Usage:
        engine = EmpathyEngine()
        result = engine.analyze(text="I'm fine", audio_file="stressed.wav")
    """

    def __init__(self):
        """Initialize the analyzers"""
        self.text_analyzer = TextAnalyzer()
        self.voice_analyzer = VoiceAnalyzer()
        self.fusion = EmotionFusion()

    def analyze_text(self, text, force_full=False):
        """
        Analyze text for emotion.

        Args:
            text: The text to analyze
            force_full: Use full transformer analysis (slower but better)

        Returns:
            dict with emotion, sentiment, confidence, etc.
        """
        return self.text_analyzer.analyze(text, force_full=force_full)

    def analyze_voice(self, audio_file):
        """
        Analyze voice audio for emotion.

        Args:
            audio_file: Path to WAV audio file

        Returns:
            dict with prosody emotion, features, confidence
        """
        return self.voice_analyzer.analyze(audio_file)

    def analyze(self, text=None, audio_file=None):
        """
        Analyze BOTH text and voice together (THE MAGIC).

        This is where the cross-modality fusion happens - if text says
        one thing but voice says another, it catches that!

        Args:
            text: Text to analyze (optional)
            audio_file: Path to audio file (optional)

        Returns:
            Complete analysis with fusion results
        """
        result = {}

        # Analyze text if provided
        if text:
            text_result = self.analyze_text(text)
            result['text_analysis'] = text_result

        # Analyze voice if provided
        if audio_file:
            voice_result = self.analyze_voice(audio_file)
            result['voice_analysis'] = voice_result

        # Fuse them if we have both
        if text and audio_file:
            fusion_result = self.fusion.fuse(
                text_analysis=result.get('text_analysis'),
                voice_analysis=result.get('voice_analysis')
            )
            result['fusion'] = fusion_result
            result['primary_emotion'] = fusion_result['fusion_emotion']
            result['confidence'] = fusion_result['fusion_confidence']
            result['authenticity'] = fusion_result['authenticity_score']
        elif text:
            # Text only
            result['primary_emotion'] = result['text_analysis']['emotion_primary']
            result['confidence'] = result['text_analysis']['emotion_confidence']
        elif audio_file:
            # Voice only
            result['primary_emotion'] = result['voice_analysis']['prosody_emotion']
            result['confidence'] = result['voice_analysis']['prosody_confidence']

        return result


if __name__ == "__main__":
    # Quick test
    engine = EmpathyEngine()

    # Test text
    print("Testing text analysis...")
    result = engine.analyze_text("I'm feeling really stressed today")
    print(f"Emotion: {result['emotion_primary']}")
    print(f"Sentiment: {result['sentiment_label']} ({result['sentiment_compound']:.2f})")
    print()

    print("✅ EmpathyEngine is working!")
