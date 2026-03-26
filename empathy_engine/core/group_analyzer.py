"""
EmpathyEngine - Group Emotion Analyzer
Analyzes collective emotional states from multiple inputs

This module handles:
- Multi-person emotion aggregation (meetings, conversations, groups)
- Dominant group emotion detection
- Emotional diversity measurement
- Outlier detection (who feels differently)
- Consensus vs conflict detection
- Group emotional momentum

Use cases:
- Meeting emotion analysis (is the team aligned?)
- Classroom mood detection
- Family therapy insights
- Customer service quality (team morale)
- Gaming squad emotional sync

Created: December 18, 2025
Part of the "all of them" expansion
"""

from typing import Dict, Optional, List, Tuple
from collections import Counter
import numpy as np


class GroupEmotionAnalyzer:
    """
    Analyzes collective emotional states from multiple individuals.

    Group metrics:
    - Dominant emotion: Most common emotion in group
    - Emotional diversity: How varied the emotions are
    - Consensus score: How aligned the group is
    - Outliers: Individuals feeling different from group
    - Group valence: Overall positive/negative mood
    - Emotional contagion: Who's influencing the group

    Usage:
        analyzer = GroupEmotionAnalyzer()

        # Analyze group of analysis results
        group_state = analyzer.analyze_group([
            person1_analysis,
            person2_analysis,
            person3_analysis
        ])
        # Returns: dominant emotion, diversity, consensus, outliers
    """

    def __init__(self):
        # Emotion valence scores
        self.emotion_valence = {
            'joy': 1.0,
            'surprise': 0.3,
            'neutral': 0.0,
            'anxiety': -0.3,
            'fear': -0.6,
            'sadness': -0.7,
            'anger': -0.8,
            'disgust': -0.9,
            # Additional
            'calm': 0.4,
            'excited': 0.8,
            'frustrated': -0.5,
            'content': 0.6
        }

    def analyze_group(
        self,
        individual_analyses: List[Dict],
        group_metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Analyze collective emotional state of a group.

        Args:
            individual_analyses: List of analysis results (one per person)
            group_metadata: Optional metadata (group_id, context, etc.)

        Returns:
            Dict with:
            - dominant_emotion: Most common emotion
            - emotion_distribution: Breakdown of all emotions
            - group_valence: Overall positive/negative (-1 to +1)
            - diversity_score: How varied emotions are (0-1)
            - consensus_score: How aligned the group is (0-1)
            - outliers: List of individuals with unusual emotions
            - intensity_avg: Average emotional intensity
            - recommendations: Insights for group facilitators
        """
        if not individual_analyses:
            return self._empty_group()

        # Extract emotions
        emotions = [
            a.get('primary_emotion', 'neutral')
            for a in individual_analyses
        ]

        # Extract sentiments
        sentiments = [
            a.get('text_analysis', {}).get('sentiment_compound', 0)
            for a in individual_analyses
        ]

        # Extract intensities (if available)
        intensities = [
            a.get('intensity', {}).get('intensity', 0.5)
            if 'intensity' in a else 0.5
            for a in individual_analyses
        ]

        # Calculate metrics
        emotion_dist = Counter(emotions)
        dominant_emotion = emotion_dist.most_common(1)[0][0]

        group_valence = self._calculate_group_valence(emotions, sentiments)
        diversity = self._calculate_diversity(emotions)
        consensus = self._calculate_consensus(emotions, sentiments)
        outliers = self._detect_outliers(individual_analyses, dominant_emotion, group_valence)
        intensity_avg = np.mean(intensities)

        # Detect emotional clusters (subgroups with different emotions)
        clusters = self._detect_clusters(individual_analyses)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            dominant_emotion,
            diversity,
            consensus,
            outliers,
            group_valence
        )

        return {
            'group_size': len(individual_analyses),
            'dominant_emotion': dominant_emotion,
            'emotion_distribution': dict(emotion_dist),
            'group_valence': round(group_valence, 3),
            'diversity_score': round(diversity, 3),
            'consensus_score': round(consensus, 3),
            'outliers': outliers,
            'emotional_clusters': clusters,
            'intensity_avg': round(intensity_avg, 3),
            'recommendations': recommendations,
            'interpretation': self._generate_interpretation(
                dominant_emotion,
                consensus,
                diversity,
                group_valence
            )
        }

    def detect_emotional_contagion(
        self,
        time_series_data: List[List[Dict]],
        individual_ids: Optional[List[str]] = None
    ) -> Dict:
        """
        Detect emotional contagion (who influences the group's emotions).

        Args:
            time_series_data: List of group snapshots over time
                              [[person1_t1, person2_t1], [person1_t2, person2_t2], ...]
            individual_ids: Optional IDs for tracking individuals

        Returns:
            Dict with influence scores for each individual
        """
        if len(time_series_data) < 2:
            return {'status': 'insufficient_data'}

        # Track emotion changes
        influence_scores = {}

        # Simple heuristic: If person A's emotion at time T matches
        # multiple people's emotions at time T+1, person A is influential

        for i in range(len(time_series_data) - 1):
            current_snapshot = time_series_data[i]
            next_snapshot = time_series_data[i + 1]

            for person_idx, person_current in enumerate(current_snapshot):
                person_id = individual_ids[person_idx] if individual_ids else f"person_{person_idx}"
                person_emotion = person_current.get('primary_emotion')

                # Count how many others shifted to this emotion
                matches = 0
                for other_idx, other_next in enumerate(next_snapshot):
                    if other_idx != person_idx:
                        if other_next.get('primary_emotion') == person_emotion:
                            matches += 1

                # Accumulate influence score
                if person_id not in influence_scores:
                    influence_scores[person_id] = 0
                influence_scores[person_id] += matches

        # Normalize scores
        if influence_scores:
            max_score = max(influence_scores.values())
            if max_score > 0:
                influence_scores = {
                    pid: round(score / max_score, 3)
                    for pid, score in influence_scores.items()
                }

        # Rank by influence
        ranked = sorted(influence_scores.items(), key=lambda x: x[1], reverse=True)

        return {
            'influence_scores': dict(ranked),
            'most_influential': ranked[0] if ranked else None,
            'interpretation': f"{ranked[0][0]} appears most emotionally influential" if ranked else "No clear influencer"
        }

    def _calculate_group_valence(self, emotions: List[str], sentiments: List[float]) -> float:
        """Calculate overall group emotional valence."""
        # Combine emotion valence and sentiment
        emotion_vals = [self.emotion_valence.get(e, 0) for e in emotions]

        # Average of emotion valence and sentiment
        avg_emotion_val = np.mean(emotion_vals)
        avg_sentiment = np.mean(sentiments)

        # Weighted combination (60% emotion, 40% sentiment)
        return 0.6 * avg_emotion_val + 0.4 * avg_sentiment

    def _calculate_diversity(self, emotions: List[str]) -> float:
        """
        Calculate emotional diversity.

        High diversity = many different emotions
        Low diversity = everyone feels similar
        """
        unique_emotions = len(set(emotions))
        max_possible = len(emotions)

        if max_possible == 0:
            return 0.0

        # Normalize to 0-1
        diversity = unique_emotions / min(max_possible, 7)  # Max 7 base emotions

        return min(1.0, diversity)

    def _calculate_consensus(self, emotions: List[str], sentiments: List[float]) -> float:
        """
        Calculate group consensus.

        High consensus = everyone aligned
        Low consensus = fragmented emotions
        """
        # Emotion consensus
        emotion_counts = Counter(emotions)
        most_common_count = emotion_counts.most_common(1)[0][1]
        emotion_consensus = most_common_count / len(emotions)

        # Sentiment consensus (low variance = high consensus)
        sentiment_std = np.std(sentiments)
        # Convert std to consensus (lower std = higher consensus)
        sentiment_consensus = max(0, 1 - (sentiment_std / 1.0))  # Normalize by max expected std

        # Combined consensus (70% emotion, 30% sentiment)
        return 0.7 * emotion_consensus + 0.3 * sentiment_consensus

    def _detect_outliers(
        self,
        individual_analyses: List[Dict],
        dominant_emotion: str,
        group_valence: float
    ) -> List[Dict]:
        """
        Detect individuals whose emotions differ significantly from group.
        """
        outliers = []

        for idx, analysis in enumerate(individual_analyses):
            person_emotion = analysis.get('primary_emotion', 'neutral')
            person_sentiment = analysis.get('text_analysis', {}).get('sentiment_compound', 0)

            # Calculate person's valence
            person_valence = self.emotion_valence.get(person_emotion, 0) * 0.6 + person_sentiment * 0.4

            # Check if different from dominant emotion
            emotion_mismatch = person_emotion != dominant_emotion

            # Check if valence differs significantly
            valence_diff = abs(person_valence - group_valence)
            valence_outlier = valence_diff > 0.5

            if emotion_mismatch and valence_outlier:
                outliers.append({
                    'person_index': idx,
                    'emotion': person_emotion,
                    'valence': round(person_valence, 2),
                    'deviation': round(valence_diff, 2),
                    'note': f"Feeling {person_emotion} while group feels {dominant_emotion}"
                })

        return outliers

    def _detect_clusters(self, individual_analyses: List[Dict]) -> List[Dict]:
        """
        Detect emotional subgroups within the larger group.

        Example: 5 people happy, 3 people anxious = 2 clusters
        """
        emotions = [a.get('primary_emotion', 'neutral') for a in individual_analyses]
        emotion_groups = Counter(emotions)

        clusters = []

        for emotion, count in emotion_groups.most_common():
            if count >= 2:  # At least 2 people to form a cluster
                percentage = count / len(emotions)

                clusters.append({
                    'emotion': emotion,
                    'size': count,
                    'percentage': round(percentage, 3),
                    'description': f"{count} people feeling {emotion} ({percentage:.0%})"
                })

        return clusters

    def _generate_recommendations(
        self,
        dominant_emotion: str,
        diversity: float,
        consensus: float,
        outliers: List[Dict],
        valence: float
    ) -> List[str]:
        """Generate actionable recommendations for group facilitators."""
        recommendations = []

        # Low consensus
        if consensus < 0.5:
            recommendations.append("⚠️ Low group consensus - consider addressing diverse emotional needs")

        # High diversity
        if diversity > 0.7:
            recommendations.append("📊 High emotional diversity - may need individual check-ins")

        # Outliers present
        if outliers:
            recommendations.append(f"👤 {len(outliers)} outlier(s) detected - may need individual attention")

        # Negative group valence
        if valence < -0.3:
            recommendations.append("⚠️ Overall negative group mood - consider intervention or break")

        # Specific dominant emotions
        if dominant_emotion in ['anxiety', 'fear', 'anger']:
            recommendations.append(f"⚠️ Group experiencing {dominant_emotion} - address concerns or provide support")

        if dominant_emotion == 'neutral' and diversity < 0.3:
            recommendations.append("😐 Group seems disengaged - consider energizing activity")

        # Positive situations
        if valence > 0.5 and consensus > 0.7:
            recommendations.append("✅ Strong positive alignment - good time to build on momentum")

        if not recommendations:
            recommendations.append("✓ Group emotional state appears balanced")

        return recommendations

    def _generate_interpretation(
        self,
        dominant_emotion: str,
        consensus: float,
        diversity: float,
        valence: float
    ) -> str:
        """Generate human-readable interpretation."""
        parts = []

        # Dominant emotion
        parts.append(f"Group primarily feeling {dominant_emotion}")

        # Consensus level
        if consensus > 0.7:
            parts.append("with strong agreement")
        elif consensus > 0.4:
            parts.append("with moderate agreement")
        else:
            parts.append("with low agreement")

        # Valence
        if valence > 0.3:
            parts.append("(overall positive mood)")
        elif valence < -0.3:
            parts.append("(overall negative mood)")

        return " ".join(parts)

    def _empty_group(self) -> Dict:
        """Return structure for empty group."""
        return {
            'group_size': 0,
            'dominant_emotion': None,
            'emotion_distribution': {},
            'group_valence': 0.0,
            'diversity_score': 0.0,
            'consensus_score': 0.0,
            'outliers': [],
            'emotional_clusters': [],
            'intensity_avg': 0.0,
            'recommendations': ['No group data available'],
            'interpretation': 'No individuals analyzed'
        }
