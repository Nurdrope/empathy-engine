"""
Comprehensive Example: EmpathyEngine Advanced Features
Demonstrates all 12 new enhancement modules

December 18, 2025 - "ALL OF THEM" expansion complete!
"""

from datetime import datetime, timedelta
import json

from empathy_engine import EmpathyEngine


def create_sample_history():
    """Generate fake historical entries for testing."""
    now = datetime.now()
    entries = []

    emotions_cycle = ['joy', 'neutral', 'anxiety', 'sadness', 'calm', 'joy']
    sentiments_cycle = [0.6, 0.1, -0.4, -0.6, 0.3, 0.7]

    for i in range(30):
        timestamp = (now - timedelta(days=29 - i, hours=14)).isoformat()
        emotion = emotions_cycle[i % len(emotions_cycle)]
        sentiment = sentiments_cycle[i % len(sentiments_cycle)]

        entries.append({
            'timestamp': timestamp,
            'text': f'Sample entry {i}',
            'emotion_primary': emotion,
            'sentiment_compound': sentiment,
            'keywords_json': json.dumps(['work', 'stress', 'weekend', 'relaxed'][i % 4:i % 4 + 1])
        })

    return entries


def main():
    # Initialize engine
    engine = EmpathyEngine()

    print("=" * 80)
    print("EMPATHYENGINE ADVANCED FEATURES - COMPREHENSIVE DEMO")
    print("=" * 80)
    print()

    historical_entries = create_sample_history()

    # =============================================================================
    # TEST 1: INTENSITY CALIBRATOR
    # =============================================================================
    print("1. INTENSITY CALIBRATOR")
    print("-" * 80)

    analysis = engine.analyze_text("I'm EXTREMELY frustrated with this!!!")
    intensity = engine.intensity_calibrator.calibrate(analysis)

    print("Text: 'I'm EXTREMELY frustrated with this!!!'")
    print(f"Emotion: {analysis['emotion_primary']}")
    print(f"Intensity Score: {intensity['intensity']} ({intensity['level']})")
    print(f"Confidence: {intensity['confidence']}")
    print(f"Factors: {list(intensity['factors'].keys())}")
    print()

    # =============================================================================
    # TEST 2: SARCASM DETECTOR
    # =============================================================================
    print("2. SARCASM DETECTOR")
    print("-" * 80)

    sarcastic_text = "Oh great, another Monday morning meeting. Just what I needed."
    analysis_sarcasm = engine.analyze_text(sarcastic_text)
    sarcasm = engine.sarcasm_detector.detect(analysis_sarcasm)

    print(f"Text: '{sarcastic_text}'")
    print(f"Sarcasm Detected: {sarcasm['sarcasm_detected']}")
    print(f"Confidence: {sarcasm['confidence']}")
    print(f"Indicators: {sarcasm['indicators'][:2] if sarcasm['indicators'] else 'None'}")
    if sarcasm['inverted_emotion']:
        print(f"True Emotion (inverted): {sarcasm['inverted_emotion']}")
    print()

    # =============================================================================
    # TEST 3: CRISIS/RISK DETECTOR
    # =============================================================================
    print("3. CRISIS/RISK DETECTOR")
    print("-" * 80)

    crisis_text = "I can't take this anymore. Everything feels hopeless."
    analysis_crisis = engine.analyze_text(crisis_text)
    risk = engine.crisis_detector.assess_risk(analysis_crisis, entries=historical_entries)

    print(f"Text: '{crisis_text}'")
    print(f"Risk Level: {risk['level']}")
    print(f"Risk Score: {risk['score']}")
    print(f"Indicators: {len(risk['indicators'])} detected")
    print(f"Recommendations: {risk['recommendations'][0]}")
    print()

    # =============================================================================
    # TEST 4: BASELINE PROFILER
    # =============================================================================
    print("4. BASELINE PROFILER")
    print("-" * 80)

    baseline = engine.baseline_profiler.build_baseline(historical_entries)

    print("Baseline Built:")
    print(f"  Entry Count: {baseline['metadata']['entry_count']}")
    print(f"  Most Common Emotion: {baseline['emotions']['most_common']}")
    print(f"  Avg Sentiment: {baseline['sentiment']['mean']}")
    print(f"  Sufficient Data: {baseline['metadata']['sufficient_data']}")

    # Compare current to baseline
    deviation = engine.baseline_profiler.compare_to_baseline(analysis, baseline)
    print("\nDeviation from Baseline:")
    print(f"  Is Deviation: {deviation['is_deviation']}")
    print(f"  Severity: {deviation['severity']}")
    print(f"  Interpretation: {deviation['interpretation']}")
    print()

    # =============================================================================
    # TEST 5: TRANSITION TRACKER
    # =============================================================================
    print("5. TRANSITION TRACKER")
    print("-" * 80)

    transitions = engine.transition_tracker.analyze_transitions(historical_entries)

    print("Transition Patterns:")
    print(f"  Total Transitions: {transitions['total_transitions']}")
    print(f"  Common Transitions: {len(transitions['common_transitions'])}")
    if transitions['common_transitions']:
        top = transitions['common_transitions'][0]
        print(f"  Most Common: {top['description']}")
    print(f"  Emotional Momentum: {transitions['emotional_momentum']['interpretation']}")
    print()

    # =============================================================================
    # TEST 6: CONTEXTUAL MODIFIER
    # =============================================================================
    print("6. CONTEXTUAL MODIFIER")
    print("-" * 80)

    work_text = "Feeling stressed about the deadline tomorrow"
    analysis_context = engine.analyze_text(work_text)
    contextualized = engine.contextual_modifier.apply_context(
        analysis_context,
        recent_entries=historical_entries[:5]
    )

    print(f"Text: '{work_text}'")
    print(f"Original Emotion: {contextualized['original_emotion']}")
    print(f"Contextualized: {contextualized['contextualized_emotion']}")
    print(f"Contexts Detected: {len(contextualized['context_detected'])}")
    print(f"Interpretation: {contextualized['interpretation']}")
    print()

    # =============================================================================
    # TEST 7: CONGRUENCE CHECKER
    # =============================================================================
    print("7. CONGRUENCE CHECKER")
    print("-" * 80)

    congruence = engine.congruence_checker.check_congruence(
        analysis,
        intensity_result=intensity,
        sarcasm_result=sarcasm,
        context_result=contextualized,
        baseline_deviation=deviation
    )

    print("Congruence Analysis:")
    print(f"  Score: {congruence['score']} ({congruence['level']})")
    print(f"  Dimensions Checked: {congruence['dimensions_checked']}")
    print(f"  Strengths: {len(congruence['strengths'])}")
    print(f"  Weaknesses: {len(congruence['weaknesses'])}")
    print(f"  Recommendation: {congruence['recommendation']}")
    print()

    # =============================================================================
    # TEST 8: EMOTION PREDICTOR
    # =============================================================================
    print("8. EMOTION PREDICTOR")
    print("-" * 80)

    # Learn patterns first
    learn_result = engine.emotion_predictor.learn_patterns(historical_entries, baseline=baseline)
    print("Learned Patterns:")
    print(f"  Transition patterns: {learn_result['transition_patterns']}")
    print(f"  Time patterns: {learn_result['time_patterns']}")

    # Predict next emotion
    prediction = engine.emotion_predictor.predict_next(analysis, timeframe='short')
    print("\nPrediction:")
    if prediction['emotion']:
        print(f"  Next Emotion: {prediction['emotion']}")
        print(f"  Confidence: {prediction['confidence']}")
        print(f"  Timeframe: {prediction['timeframe']}")
        print(f"  Method: {prediction['method']}")
    else:
        print(f"  {prediction['interpretation']}")
    print()

    # =============================================================================
    # TEST 9: TRIGGER IDENTIFIER
    # =============================================================================
    print("9. TRIGGER IDENTIFIER")
    print("-" * 80)

    triggers = engine.trigger_identifier.identify_triggers(historical_entries)

    print("Identified Triggers:")
    if triggers.get('event_triggers'):
        print(f"  Event Triggers: {len(triggers['event_triggers'])}")
        if triggers['event_triggers']:
            print(f"    Example: {triggers['event_triggers'][0]['description']}")

    if triggers.get('positive_triggers'):
        print(f"  Positive Triggers: {len(triggers['positive_triggers'])}")

    if triggers.get('negative_triggers'):
        print(f"  Negative Triggers: {len(triggers['negative_triggers'])}")
    print()

    # =============================================================================
    # TEST 10: GROUP EMOTION ANALYZER
    # =============================================================================
    print("10. GROUP EMOTION ANALYZER")
    print("-" * 80)

    # Simulate group of 5 people
    group_analyses = []
    for i in range(5):
        emotions = ['joy', 'joy', 'neutral', 'anxiety', 'joy']
        person_analysis = {
            'primary_emotion': emotions[i],
            'text_analysis': {'sentiment_compound': [0.5, 0.6, 0.1, -0.3, 0.7][i]},
            'confidence': 0.8
        }
        group_analyses.append(person_analysis)

    group_state = engine.group_analyzer.analyze_group(group_analyses)

    print("Group Analysis (5 people):")
    print(f"  Dominant Emotion: {group_state['dominant_emotion']}")
    print(f"  Group Valence: {group_state['group_valence']}")
    print(f"  Consensus Score: {group_state['consensus_score']}")
    print(f"  Diversity Score: {group_state['diversity_score']}")
    print(f"  Outliers: {len(group_state['outliers'])}")
    print(f"  Recommendations: {group_state['recommendations'][0]}")
    print()

    # =============================================================================
    # TEST 11: CULTURAL ADAPTER
    # =============================================================================
    print("11. CULTURAL ADAPTER")
    print("-" * 80)

    british_text = "I'm not thrilled about this situation, quite frankly."
    analysis_cultural = engine.analyze_text(british_text)

    # Set British cultural profile
    uk_profile = engine.cultural_adapter.set_cultural_profile(language='en', region='UK')

    adapted = engine.cultural_adapter.adapt(
        analysis_cultural,
        cultural_profile=uk_profile,
        auto_detect=False
    )

    print(f"Text: '{british_text}'")
    print(f"Cultural Profile: {adapted['cultural_profile'].get('region', 'Auto-detected')}")
    print(f"Original Emotion: {adapted['original_emotion']}")
    print(f"Adapted Emotion: {adapted['adapted_emotion']}")
    print(f"Original Intensity: {adapted['original_intensity']}")
    print(f"Adapted Intensity: {adapted['adapted_intensity']}")
    print(f"Cultural Notes: {len(adapted['cultural_notes'])}")
    print()

    # =============================================================================
    # TEST 12: COHERENCE SCORER
    # =============================================================================
    print("12. COHERENCE SCORER")
    print("-" * 80)

    coherence = engine.coherence_scorer.score_coherence(
        analysis,
        intensity_result=intensity,
        sarcasm_result=sarcasm,
        congruence_result=congruence,
        context_result=contextualized,
        baseline_deviation=deviation,
        cultural_adaptation=adapted
    )

    print("Overall Coherence Assessment:")
    print(f"  Score: {coherence['score']} ({coherence['level']})")
    print(f"  Reliability: {coherence['reliability']}")
    print(f"  Dimensions Scored: {len(coherence['dimension_scores'])}")
    print(f"  Strengths: {coherence['strengths'][:2] if coherence['strengths'] else 'None'}")
    print(f"  Weaknesses: {coherence['weaknesses'][:2] if coherence['weaknesses'] else 'None'}")
    print(f"  Recommendation: {coherence['recommendation']}")
    print()

    # =============================================================================
    # SUMMARY
    # =============================================================================
    print("=" * 80)
    print("SUMMARY - ALL 12 ADVANCED MODULES TESTED")
    print("=" * 80)
    print()
    print("✅ Intensity Calibrator - Emotion intensity scoring")
    print("✅ Sarcasm Detector - Irony and inverted emotions")
    print("✅ Crisis/Risk Detector - Mental health risk assessment")
    print("✅ Baseline Profiler - Personal emotional profiling")
    print("✅ Transition Tracker - Emotion flow patterns")
    print("✅ Contextual Modifier - Situational emotion adjustment")
    print("✅ Congruence Checker - Multi-dimensional consistency")
    print("✅ Emotion Predictor - Future state forecasting")
    print("✅ Trigger Identifier - Event-emotion correlations")
    print("✅ Group Analyzer - Collective emotional intelligence")
    print("✅ Cultural Adapter - Cross-cultural interpretation")
    print("✅ Coherence Scorer - Overall quality assessment")
    print()
    print("=" * 80)
    print("EMPATHYENGINE: FROM GOOD TO UNREAL ENGINE LEVEL")
    print("=" * 80)
    print()
    print("These 12 modules transform EmpathyEngine from a solid emotional")
    print("analysis library into a COMPREHENSIVE emotional intelligence platform.")
    print()
    print("Ready for:")
    print("  - Personal wellness apps (MoodRing)")
    print("  - Therapeutic AI systems")
    print("  - Gaming emotion engines")
    print("  - Automotive emotional UX")
    print("  - Wearable emotional tracking")
    print("  - Meeting/group dynamics")
    print("  - Cross-cultural communication")
    print("  - Crisis intervention tools")
    print()
    print("🚀 The future of emotional AI is here. Let's ship it. 🚀")
    print("=" * 80)


if __name__ == "__main__":
    main()
