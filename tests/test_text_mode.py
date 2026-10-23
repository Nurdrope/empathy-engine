"""Which text analysis runs: the emotion model vs. quick sentiment mapping."""

import json
from pathlib import Path

import pytest

from empathy_engine.core.text_analyzer import TextAnalyzer

SHORT = "I'm really anxious about the appointment tomorrow."
MODEL_CACHED = (Path.home() / ".cache/huggingface/hub/models--j-hartmann--emotion-english-distilroberta-base").exists()


@pytest.fixture
def analyzer(monkeypatch):
    t = TextAnalyzer()
    calls = []

    def fake_model(text):
        calls.append(text)
        return {"emotion_primary": "fear", "emotion_confidence": 0.99,
                "emotions_json": json.dumps({"fear": 0.99}), "analysis_mode": "full"}

    monkeypatch.setattr(t, "analyze_emotions", fake_model)
    t.model_calls = calls
    return t


def set_ml(monkeypatch, available):
    monkeypatch.setattr(TextAnalyzer, "ml_available", staticmethod(lambda: available))


def test_short_text_uses_model_when_ml_installed(analyzer, monkeypatch):
    set_ml(monkeypatch, True)
    result = analyzer.analyze(SHORT)
    assert analyzer.model_calls == [SHORT]
    assert result["emotion_primary"] == "fear"
    assert result["analysis_mode"] == "full"


def test_short_text_uses_quick_mode_without_ml(analyzer, monkeypatch):
    set_ml(monkeypatch, False)
    result = analyzer.analyze(SHORT)
    assert analyzer.model_calls == []
    assert result["analysis_mode"] == "quick"
    assert result["emotion_primary"] in {"joy", "sadness", "neutral"}  # all quick mode can say


def test_force_full_still_tries_model_without_ml(analyzer, monkeypatch):
    set_ml(monkeypatch, False)
    analyzer.analyze(SHORT, force_full=True)
    assert analyzer.model_calls == [SHORT]


def test_long_text_always_tries_model(analyzer, monkeypatch):
    set_ml(monkeypatch, False)
    analyzer.analyze(" ".join(["word"] * 25))
    assert len(analyzer.model_calls) == 1


def test_model_failure_is_labelled_fallback(monkeypatch):
    t = TextAnalyzer()

    def broken():
        raise RuntimeError("model unavailable")

    monkeypatch.setattr(t, "_load_emotion_classifier", broken)
    result = t.analyze_emotions(SHORT)
    assert result["analysis_mode"] == "quick-fallback"


def test_ml_available_is_cheap_and_boolean():
    assert isinstance(TextAnalyzer.ml_available(), bool)


@pytest.mark.skipif(not (TextAnalyzer.ml_available() and MODEL_CACHED),
                    reason="needs the [ml] extra and the cached emotion model")
@pytest.mark.parametrize("text,emotion", [
    ("I'm really anxious about the appointment tomorrow and I can't sleep.", "fear"),
    ("I'm so angry at how they treated me at work today.", "anger"),
    ("That was disgusting, I can't believe he did that.", "disgust"),
])
def test_real_model_on_short_texts(text, emotion):
    # Default call, no force_full: these are under 20 words.
    result = TextAnalyzer().analyze(text)
    assert result["analysis_mode"] == "full"
    assert result["emotion_primary"] == emotion
