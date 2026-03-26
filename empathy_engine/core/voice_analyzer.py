"""
EmpathyEngine - Voice Prosody Analysis Module
Analyzes intonation, pitch, rhythm, stress, and tone to detect emotions

Extracted from MoodRing (Nov 2025)
"""

import json
import numpy as np
import librosa
import warnings
from typing import Dict, Optional, Tuple
from ..utils.logging import get_logger
from ..utils.settings import get_settings
warnings.filterwarnings('ignore')
try:
    import opensmile
except ImportError:
    opensmile = None
try:
    import parselmouth
except ImportError:
    parselmouth = None


logger = get_logger(__name__)
settings = get_settings()


class VoiceAnalyzer:
    """
    Analyzes prosodic features of voice recordings to detect emotional state.

    Emotions detected:
    - calm: low pitch variance, steady rhythm, moderate energy
    - sad: low pitch, slow rhythm, low energy
    - frustrated: moderate-high pitch, irregular rhythm, moderate-high energy
    - elevated: high pitch, moderate-fast rhythm, high energy
    - angry: high pitch, high energy, high variance, fast rhythm
    - excited: high pitch, fast rhythm, high energy, high variance
    - neutral: moderate everything, low variance
    """

    def __init__(self):
        # Emotion thresholds (tuned based on typical speech patterns)
        self.emotion_profiles = {
            'calm': {
                'pitch_mean': (80, 180),      # Hz - low to moderate
                'pitch_std': (0, 25),         # Low variance
                'energy_mean': (0.01, 0.15),  # Moderate-low energy
                'speech_rate': (2, 4),        # syllables/sec - slow to moderate
                'spectral_centroid': (0, 2000)  # Hz - warm tone
            },
            'sad': {
                'pitch_mean': (75, 150),      # Low pitch
                'pitch_std': (0, 20),         # Low variance
                'energy_mean': (0.005, 0.10), # Low energy
                'speech_rate': (1.5, 3),      # Slow
                'spectral_centroid': (0, 1800)  # Warm, dark tone
            },
            'frustrated': {
                'pitch_mean': (150, 250),     # Moderate-high pitch
                'pitch_std': (25, 60),        # Moderate-high variance
                'energy_mean': (0.10, 0.30),  # Moderate-high energy
                'speech_rate': (3, 5),        # Moderate-fast, irregular
                'spectral_centroid': (1800, 3500)  # Tense tone
            },
            'elevated': {
                'pitch_mean': (180, 280),     # High pitch
                'pitch_std': (20, 50),        # Moderate variance
                'energy_mean': (0.15, 0.40),  # High energy
                'speech_rate': (4, 6),        # Fast
                'spectral_centroid': (2000, 4000)  # Bright tone
            },
            'angry': {
                'pitch_mean': (160, 300),     # High pitch
                'pitch_std': (30, 80),        # High variance
                'energy_mean': (0.20, 0.50),  # Very high energy
                'speech_rate': (4.5, 7),      # Fast, choppy
                'spectral_centroid': (2500, 5000)  # Harsh, bright tone
            },
            'excited': {
                'pitch_mean': (180, 320),     # High pitch
                'pitch_std': (40, 90),        # High variance (animated)
                'energy_mean': (0.20, 0.45),  # High energy
                'speech_rate': (5, 8),        # Very fast
                'spectral_centroid': (2200, 4500)  # Very bright tone
            },
            'neutral': {
                'pitch_mean': (100, 200),     # Moderate pitch
                'pitch_std': (10, 30),        # Low-moderate variance
                'energy_mean': (0.05, 0.20),  # Moderate energy
                'speech_rate': (3, 5),        # Normal pace
                'spectral_centroid': (1500, 2500)  # Neutral tone
            }
        }
        self._opensmile = None

    def _load_opensmile(self):
        """Load openSMILE feature extractor if enabled."""
        if not settings.enable_opensmile or not opensmile:
            return None
        if self._opensmile is None:
            self._opensmile = opensmile.Smile(
                feature_set=opensmile.FeatureSet.eGeMAPSv02,
                feature_level=opensmile.FeatureLevel.Functionals
            )
        return self._opensmile

    def _extract_opensmile_features(self, audio_path: str) -> Dict:
        """Extract a compact openSMILE feature subset when available."""
        smile = self._load_opensmile()
        if not smile:
            return {}
        try:
            features_df = smile.process_file(audio_path)
            row = features_df.iloc[0].to_dict()
            keys = sorted(row.keys())
            selected = {k: float(row[k]) for k in keys[:10]}
            return {
                'opensmile_features_json': json.dumps(selected),
                'opensmile_feature_count': len(row)
            }
        except Exception as e:
            logger.error("openSMILE feature extraction error", error=str(e))
            return {
                'opensmile_features_json': None,
                'opensmile_feature_count': None
            }

    def _extract_praat_features(self, audio_path: str) -> Dict:
        """Extract prosody features via Praat/Parselmouth when available."""
        if not settings.enable_praat or not parselmouth:
            return {}
        try:
            sound = parselmouth.Sound(audio_path)
            pitch = sound.to_pitch()
            pitch_values = np.array(pitch.selected_array.get('frequency', []))
            pitch_values = pitch_values[pitch_values > 0]
            pitch_mean = float(np.mean(pitch_values)) if pitch_values.size else 0.0

            intensity = sound.to_intensity()
            intensity_values = intensity.values[0] if intensity.values.size else []
            intensity_mean = float(np.mean(intensity_values)) if len(intensity_values) else 0.0

            point_process = parselmouth.praat.call(sound, "To PointProcess (periodic, cc)", 75, 500)
            jitter_local = parselmouth.praat.call(point_process, "Get jitter (local)", 0, 0, 75, 500, 1.3)
            shimmer_local = parselmouth.praat.call([sound, point_process], "Get shimmer (local)", 0, 0, 75, 500, 1.3, 1.6)

            return {
                'praat_pitch_mean': pitch_mean,
                'praat_intensity_mean': intensity_mean,
                'praat_jitter_local': float(jitter_local),
                'praat_shimmer_local': float(shimmer_local)
            }
        except Exception as e:
            logger.error("Praat feature extraction error", error=str(e))
            return {
                'praat_pitch_mean': None,
                'praat_intensity_mean': None,
                'praat_jitter_local': None,
                'praat_shimmer_local': None
            }

    def extract_features(self, audio_path: str) -> Optional[Dict]:
        """
        Extract prosodic features from audio file.

        Args:
            audio_path: Path to audio file (WAV format)

        Returns:
            Dict with:
            - pitch_mean: average fundamental frequency (Hz)
            - pitch_std: pitch variance (emotional intensity)
            - pitch_range: pitch range (max - min)
            - energy_mean: average energy/loudness
            - energy_std: energy variance
            - speech_rate: estimated syllables per second
            - spectral_centroid: brightness of tone
            - zero_crossing_rate: noisiness/breathiness
            - duration: audio duration in seconds
        """
        try:
            # Load audio file
            y, sr = librosa.load(audio_path, sr=22050)

            # 1. PITCH ANALYSIS (F0 - fundamental frequency)
            pitches, magnitudes = librosa.piptrack(y=y, sr=sr, fmin=75, fmax=400)

            # Extract pitch values (only where magnitude is significant)
            pitch_values = []
            for t in range(pitches.shape[1]):
                index = magnitudes[:, t].argmax()
                pitch = pitches[index, t]
                if pitch > 0:  # Valid pitch
                    pitch_values.append(pitch)

            if len(pitch_values) == 0:
                pitch_values = [0]

            pitch_mean = np.mean(pitch_values)
            pitch_std = np.std(pitch_values)
            pitch_range = np.max(pitch_values) - np.min(pitch_values) if len(pitch_values) > 1 else 0

            # 2. ENERGY/INTENSITY ANALYSIS
            rms = librosa.feature.rms(y=y)[0]
            energy_mean = np.mean(rms)
            energy_std = np.std(rms)

            # 3. RHYTHM/SPEECH RATE (using onset detection)
            onset_frames = librosa.onset.onset_detect(y=y, sr=sr, units='frames')
            duration = librosa.get_duration(y=y, sr=sr)
            speech_rate = len(onset_frames) / duration if duration > 0 else 0

            # 4. SPECTRAL CENTROID (tone brightness/color)
            spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            spectral_centroid_mean = np.mean(spectral_centroids)

            # 5. ZERO CROSSING RATE (noisiness/stress)
            zcr = librosa.feature.zero_crossing_rate(y)[0]
            zcr_mean = np.mean(zcr)

            features = {
                'pitch_mean': float(pitch_mean),
                'pitch_std': float(pitch_std),
                'pitch_range': float(pitch_range),
                'energy_mean': float(energy_mean),
                'energy_std': float(energy_std),
                'speech_rate': float(speech_rate),
                'spectral_centroid': float(spectral_centroid_mean),
                'zero_crossing_rate': float(zcr_mean),
                'duration': float(duration)
            }

            opensmile_features = self._extract_opensmile_features(audio_path)
            if opensmile_features:
                features.update(opensmile_features)

            praat_features = self._extract_praat_features(audio_path)
            if praat_features:
                features.update(praat_features)

            return features

        except Exception as e:
            logger.error("Error extracting prosody features", error=str(e))
            return None

    def classify_emotion(self, features: Dict) -> Dict:
        """
        Classify emotion based on prosodic features.

        Args:
            features: Dict of prosodic features from extract_features()

        Returns:
            Dict with:
            - emotion: primary emotion label
            - confidence: 0-1 confidence score
            - scores: dict of all emotion scores
            - features: original features dict
        """
        if not features:
            return {
                'emotion': 'neutral',
                'confidence': 0.0,
                'scores': {},
                'features': {}
            }

        # Calculate match score for each emotion
        emotion_scores = {}

        for emotion, profile in self.emotion_profiles.items():
            score = 0.0
            matches = 0

            # Check each feature against emotion profile
            for feature_name, (min_val, max_val) in profile.items():
                if feature_name in features:
                    value = features[feature_name]

                    # Calculate how well the value fits the range
                    if min_val <= value <= max_val:
                        # Perfect match
                        score += 1.0
                        matches += 1
                    else:
                        # Partial match based on distance from range
                        if value < min_val:
                            distance = min_val - value
                            range_size = max_val - min_val
                        else:  # value > max_val
                            distance = value - max_val
                            range_size = max_val - min_val

                        # Penalize based on how far outside the range
                        penalty = min(distance / range_size, 2.0)  # Cap at 2x range
                        partial_score = max(0, 1.0 - (penalty * 0.5))
                        score += partial_score
                        matches += 1

            # Normalize score
            if matches > 0:
                emotion_scores[emotion] = score / matches
            else:
                emotion_scores[emotion] = 0.0

        # Get primary emotion (highest score)
        if emotion_scores:
            primary_emotion = max(emotion_scores.items(), key=lambda x: x[1])
            emotion_label = primary_emotion[0]
            confidence = primary_emotion[1]
        else:
            emotion_label = 'neutral'
            confidence = 0.0

        return {
            'emotion': emotion_label,
            'confidence': float(confidence),
            'scores': emotion_scores,
            'features': features
        }

    def analyze(self, audio_path: str) -> Dict:
        """
        Full prosody analysis pipeline.

        Args:
            audio_path: path to audio file (WAV format)

        Returns:
            Dict with:
            - prosody_emotion: primary emotion from voice
            - prosody_confidence: confidence score
            - prosody_scores: all emotion scores
            - prosody_features: extracted features
        """
        features = self.extract_features(audio_path)

        if not features:
            return {
                'prosody_emotion': 'neutral',
                'prosody_confidence': 0.0,
                'prosody_scores': {},
                'prosody_features': {}
            }

        classification = self.classify_emotion(features)

        return {
            'prosody_emotion': classification['emotion'],
            'prosody_confidence': classification['confidence'],
            'prosody_scores': classification['scores'],
            'prosody_features': features
        }

    def get_emotion_description(self, emotion: str) -> str:
        """
        Get human-readable description of detected emotion.

        Args:
            emotion: Emotion label

        Returns:
            Human-readable description
        """
        descriptions = {
            'calm': 'Calm and composed',
            'sad': 'Low energy, possibly sad or tired',
            'frustrated': 'Tense or frustrated',
            'elevated': 'Energetic and upbeat',
            'angry': 'Agitated or angry',
            'excited': 'Highly excited or animated',
            'neutral': 'Neutral tone'
        }
        return descriptions.get(emotion, 'Unknown')
