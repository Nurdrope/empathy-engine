"""
Runtime configuration with optional pydantic-settings support.
"""

from __future__ import annotations

from dataclasses import dataclass


try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
except Exception:
    BaseSettings = None
    SettingsConfigDict = None


if BaseSettings:
    class Settings(BaseSettings):
        api_title: str = "EmpathyEngine API"
        api_description: str = "Multi-modal emotional intelligence API"
        api_version: str = "0.1.1"
        log_level: str = "INFO"
        enable_semantic_embeddings: bool = False
        enable_spacy: bool = True
        enable_textstat: bool = True
        enable_opensmile: bool = False
        enable_praat: bool = True
        stt_command: str | None = None

        model_config = SettingsConfigDict(env_prefix="EMPATHY_ENGINE_")
else:
    @dataclass
    class Settings:
        api_title: str = "EmpathyEngine API"
        api_description: str = "Multi-modal emotional intelligence API"
        api_version: str = "0.1.1"
        log_level: str = "INFO"
        enable_semantic_embeddings: bool = False
        enable_spacy: bool = True
        enable_textstat: bool = True
        enable_opensmile: bool = False
        enable_praat: bool = True
        stt_command: str | None = None


_SETTINGS = None


def get_settings() -> Settings:
    """Singleton settings loader to avoid repeated env parsing."""
    global _SETTINGS
    if _SETTINGS is None:
        _SETTINGS = Settings()
    return _SETTINGS
