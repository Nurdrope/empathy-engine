"""
EmpathyEngine - Cultural & Linguistic Emotion Adapter
Adjusts emotion interpretation for cultural and linguistic contexts

Different cultures express emotions differently:
- Direct vs indirect communication (Western vs Eastern)
- Emotion display rules (what's acceptable to show)
- Linguistic patterns (formality, understatement, hyperbole)
- Collectivist vs individualist expression
- Context-dependent meaning

Examples:
- British: "I'm not thrilled" = very angry (understatement)
- American: "I'm pretty upset" = moderately upset (direct)
- Japanese: High formality may mask true emotion
- Spanish: More expressive language (higher baseline intensity)

Created: December 18, 2025
Part of the "all of them" expansion
"""

import re
from typing import Dict, Optional, List
from collections import Counter


class CulturalAdapter:
    """
    Adapts emotional analysis for cultural and linguistic contexts.

    Cultural factors:
    - Communication style (direct/indirect)
    - Emotion display rules
    - Formality levels
    - Expression intensity norms
    - Idioms and cultural phrases

    Usage:
        adapter = CulturalAdapter()

        # Set user's cultural context
        adapter.set_cultural_profile(
            language='en',
            region='UK',
            communication_style='indirect'
        )

        # Adapt analysis for cultural context
        adapted = adapter.adapt(analysis_result)
        # Returns adjusted emotion/intensity based on cultural norms
    """

    def __init__(self):
        # Cultural communication styles
        self.cultural_profiles = {
            'UK': {
                'communication_style': 'indirect',
                'understatement_common': True,
                'formality_high': True,
                'intensity_modifier': 0.7,  # Brits understate
                'notes': 'British tend to understate emotions'
            },
            'US': {
                'communication_style': 'direct',
                'understatement_common': False,
                'formality_high': False,
                'intensity_modifier': 1.0,
                'notes': 'American communication tends to be direct'
            },
            'JP': {
                'communication_style': 'very_indirect',
                'understatement_common': True,
                'formality_high': True,
                'intensity_modifier': 0.5,  # Very reserved
                'notes': 'Japanese culture values emotional restraint'
            },
            'DE': {
                'communication_style': 'very_direct',
                'understatement_common': False,
                'formality_high': True,
                'intensity_modifier': 1.0,
                'notes': 'German communication is very direct and literal'
            },
            'ES': {
                'communication_style': 'expressive',
                'understatement_common': False,
                'formality_high': False,
                'intensity_modifier': 1.3,  # More expressive
                'notes': 'Spanish speakers tend to be more expressive'
            },
            'MX': {
                'communication_style': 'expressive',
                'understatement_common': False,
                'formality_high': False,
                'intensity_modifier': 1.2,
                'notes': 'Mexican Spanish is warm and expressive'
            },
            'FR': {
                'communication_style': 'indirect',
                'understatement_common': True,
                'formality_high': True,
                'intensity_modifier': 0.9,
                'notes': 'French communication values subtlety'
            },
            'AU': {
                'communication_style': 'casual_direct',
                'understatement_common': True,
                'formality_high': False,
                'intensity_modifier': 0.8,  # Understated but casual
                'notes': 'Australian English is casual but understated'
            }
        }

        # Understatement phrases (particularly British)
        self.understatement_phrases = [
            r'\bnot thrilled\b',
            r'\bnot pleased\b',
            r'\bnot happy\b',
            r'\bnot great\b',
            r'\bnot ideal\b',
            r'\ba bit\b',
            r'\bslightly\b',
            r'\brather\b',
            r'\bsomewhat\b',
            r'\bquite\b'  # In British: "quite bad" = very bad
        ]

        # Formality indicators
        self.formality_markers = [
            r'\b(please|kindly|would you|could you|may I)\b',
            r'\b(sir|madam|mr|mrs|ms)\b',
            r'\b(apologize|apologise|regret|unfortunately)\b'
        ]

        # Cultural idioms that mask emotion
        self.cultural_idioms = {
            'UK': [
                (r'\bmustn\'t grumble\b', 'Actually upset but being stoic'),
                (r'\bnot bad\b', 'Actually quite good'),
                (r'\bcould be worse\b', 'Moderately satisfied'),
                (r'\bcan\'t complain\b', 'Actually content')
            ],
            'US': [
                (r'\bno worries\b', 'Casual dismissal'),
                (r'\bit\'s all good\b', 'Reassurance, possibly masking concern')
            ]
        }

    def set_cultural_profile(
        self,
        language: str = 'en',
        region: Optional[str] = None,
        communication_style: Optional[str] = None
    ) -> Dict:
        """
        Set cultural context for adaptation.

        Args:
            language: Language code (en, es, fr, de, ja, etc.)
            region: Region code (UK, US, MX, etc.)
            communication_style: Override style (direct, indirect, etc.)

        Returns:
            Active cultural profile
        """
        if region and region in self.cultural_profiles:
            profile = self.cultural_profiles[region].copy()
        else:
            # Default to US English
            profile = self.cultural_profiles.get('US', {}).copy()

        # Override communication style if specified
        if communication_style:
            profile['communication_style'] = communication_style

        profile['language'] = language
        profile['region'] = region

        return profile

    def adapt(
        self,
        analysis_result: Dict,
        cultural_profile: Optional[Dict] = None,
        auto_detect: bool = True
    ) -> Dict:
        """
        Adapt emotion analysis for cultural context.

        Args:
            analysis_result: Output from EmpathyEngine.analyze()
            cultural_profile: Cultural profile (from set_cultural_profile)
            auto_detect: Try to auto-detect cultural markers

        Returns:
            Dict with:
            - original_emotion: Unadapted emotion
            - adapted_emotion: Culturally adjusted emotion
            - original_intensity: Unadapted intensity
            - adapted_intensity: Culturally adjusted intensity
            - cultural_notes: Detected cultural patterns
            - confidence_adjustment: How cultural adaptation affects confidence
        """
        text = analysis_result.get('text_analysis', {}).get('text', '')

        if not text:
            return self._no_adaptation(analysis_result)

        # Auto-detect cultural markers if requested
        if auto_detect and not cultural_profile:
            cultural_profile = self._auto_detect_culture(text)

        if not cultural_profile:
            # Default to neutral profile
            cultural_profile = {'intensity_modifier': 1.0, 'notes': 'No cultural profile set'}

        cultural_notes = []

        # Original values
        original_emotion = analysis_result.get('primary_emotion', 'neutral')
        original_intensity = analysis_result.get('intensity', {}).get('intensity', 0.5) if 'intensity' in analysis_result else 0.5

        adapted_emotion = original_emotion
        adapted_intensity = original_intensity

        # Apply intensity modification based on cultural norms
        intensity_modifier = cultural_profile.get('intensity_modifier', 1.0)

        # Adjust intensity
        if intensity_modifier != 1.0:
            adapted_intensity = original_intensity / intensity_modifier
            adapted_intensity = max(0.0, min(1.0, adapted_intensity))  # Clamp

            if intensity_modifier < 1.0:
                cultural_notes.append(f"Intensity adjusted upward (understatement culture)")
            else:
                cultural_notes.append(f"Intensity adjusted downward (expressive culture)")

        # Check for understatement phrases
        if cultural_profile.get('understatement_common'):
            understatement_detected = self._detect_understatement(text)
            if understatement_detected:
                cultural_notes.append(understatement_detected)
                # Upgrade emotion severity
                adapted_emotion = self._upgrade_emotion(original_emotion)
                adapted_intensity = min(1.0, adapted_intensity * 1.5)

        # Check for high formality (may mask true emotion)
        formality_level = self._detect_formality(text)
        if formality_level > 0.5 and cultural_profile.get('formality_high'):
            cultural_notes.append(f"High formality detected - true emotion may be masked")

        # Check for cultural idioms
        region = cultural_profile.get('region')
        if region in self.cultural_idioms:
            idiom_match = self._detect_idioms(text, region)
            if idiom_match:
                cultural_notes.append(idiom_match)

        # Confidence adjustment
        confidence_adjustment = 0.0
        if cultural_notes:
            # More cultural markers = less confidence in raw analysis
            confidence_adjustment = -0.1 * len(cultural_notes)

        return {
            'original_emotion': original_emotion,
            'adapted_emotion': adapted_emotion,
            'original_intensity': round(original_intensity, 3),
            'adapted_intensity': round(adapted_intensity, 3),
            'cultural_notes': cultural_notes,
            'cultural_profile': cultural_profile,
            'confidence_adjustment': round(confidence_adjustment, 3),
            'interpretation': self._generate_interpretation(
                original_emotion,
                adapted_emotion,
                original_intensity,
                adapted_intensity,
                cultural_profile
            )
        }

    def _auto_detect_culture(self, text: str) -> Optional[Dict]:
        """
        Attempt to auto-detect cultural context from text.

        Limited detection based on:
        - British spellings (colour, favour, etc.)
        - Regional slang
        - Formality levels
        """
        text_lower = text.lower()

        # British spelling indicators
        british_patterns = [
            r'\bcolour\b', r'\bfavour\b', r'\bhonour\b',
            r'\bcentre\b', r'\bmetre\b', r'\blicence\b',
            r'\borganise\b', r'\brealise\b'
        ]

        if any(re.search(p, text_lower) for p in british_patterns):
            return self.cultural_profiles['UK']

        # High formality might suggest British/Japanese
        formality = self._detect_formality(text)
        if formality > 0.7:
            return {
                'communication_style': 'formal',
                'intensity_modifier': 0.8,
                'notes': 'Auto-detected: High formality communication'
            }

        return None

    def _detect_understatement(self, text: str) -> Optional[str]:
        """Detect understatement phrases."""
        text_lower = text.lower()

        for pattern in self.understatement_phrases:
            if re.search(pattern, text_lower):
                return f"Understatement detected: '{re.search(pattern, text_lower).group()}'"

        return None

    def _detect_formality(self, text: str) -> float:
        """
        Detect formality level (0-1).

        0 = very casual
        1 = very formal
        """
        text_lower = text.lower()

        formality_score = 0.0

        # Check formality markers
        for pattern in self.formality_markers:
            matches = len(re.findall(pattern, text_lower))
            formality_score += matches * 0.2

        # Check for contractions (informal)
        contractions = len(re.findall(r"n\'t|\'re|\'ve|\'ll|\'d", text_lower))
        formality_score -= contractions * 0.1

        return max(0.0, min(1.0, formality_score))

    def _detect_idioms(self, text: str, region: str) -> Optional[str]:
        """Detect cultural idioms."""
        text_lower = text.lower()

        if region in self.cultural_idioms:
            for pattern, meaning in self.cultural_idioms[region]:
                if re.search(pattern, text_lower):
                    return f"Cultural idiom: '{re.search(pattern, text_lower).group()}' - {meaning}"

        return None

    def _upgrade_emotion(self, emotion: str) -> str:
        """
        Upgrade emotion severity (for understatement cultures).

        Example: 'neutral' → 'anxiety', 'sadness' → 'very sad'
        """
        upgrades = {
            'neutral': 'anxiety',
            'anxiety': 'fear',
            'sadness': 'deep_sadness',
            'anger': 'fury',
            'joy': 'joy'  # Don't downgrade positive
        }

        return upgrades.get(emotion, emotion)

    def _generate_interpretation(
        self,
        original_emotion: str,
        adapted_emotion: str,
        original_intensity: float,
        adapted_intensity: float,
        profile: Dict
    ) -> str:
        """Generate human-readable interpretation."""
        if original_emotion == adapted_emotion and abs(original_intensity - adapted_intensity) < 0.1:
            return f"No cultural adjustment needed - {profile.get('notes', '')}"

        parts = []

        if original_emotion != adapted_emotion:
            parts.append(f"Emotion adjusted: {original_emotion} → {adapted_emotion}")

        if abs(original_intensity - adapted_intensity) >= 0.1:
            direction = "increased" if adapted_intensity > original_intensity else "decreased"
            parts.append(f"Intensity {direction}: {original_intensity:.2f} → {adapted_intensity:.2f}")

        parts.append(f"({profile.get('notes', 'Cultural adaptation applied')})")

        return " | ".join(parts)

    def _no_adaptation(self, analysis: Dict) -> Dict:
        """Return structure when no adaptation applied."""
        emotion = analysis.get('primary_emotion', 'neutral')
        intensity = analysis.get('intensity', {}).get('intensity', 0.5) if 'intensity' in analysis else 0.5

        return {
            'original_emotion': emotion,
            'adapted_emotion': emotion,
            'original_intensity': intensity,
            'adapted_intensity': intensity,
            'cultural_notes': [],
            'cultural_profile': None,
            'confidence_adjustment': 0.0,
            'interpretation': 'No cultural adaptation applied'
        }
