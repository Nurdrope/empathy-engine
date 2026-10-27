"""
Security settings and guards for the EmpathyEngine API.

Read straight from environment variables (not utils.settings) so they work
whether or not pydantic-settings is installed:

    EMPATHY_ENGINE_API_KEYS               comma-separated keys clients must send
                                          (Authorization: Bearer <key> or X-API-Key)
    EMPATHY_ENGINE_ALLOW_UNAUTHENTICATED  "1" = no keys needed (local development only)
    EMPATHY_ENGINE_CORS_ORIGINS           comma-separated browser origins allowed to call
                                          the API (default: none)
    EMPATHY_ENGINE_MAX_UPLOAD_MB          largest audio upload (default 25)
    EMPATHY_ENGINE_MAX_BODY_MB            largest JSON/form body (default 2)
    EMPATHY_ENGINE_SUBPROCESS_TIMEOUT     seconds before ffmpeg/STT are killed (default 120)

Generate a key with:
    python -c "import secrets; print(secrets.token_urlsafe(32))"
"""

from __future__ import annotations

import hmac
import os
from dataclasses import dataclass, field
from typing import Mapping, Optional

from fastapi import HTTPException

MIN_KEY_LENGTH = 16

# Reachable without a key: liveness checks and the API docs (the API surface
# is public in the open-source repo anyway). Everything else needs a key, so a
# newly added endpoint is protected by default.
PUBLIC_PATHS = frozenset({"/", "/health", "/docs", "/docs/oauth2-redirect", "/redoc", "/openapi.json"})

# Formats the upload endpoints accept. The suffix ends up in a temp filename
# that is handed to ffmpeg / the STT command, so only known-safe values pass.
ALLOWED_AUDIO_SUFFIXES = frozenset({".wav", ".mp3", ".m4a", ".ogg", ".oga", ".opus", ".flac", ".webm", ".aac"})

_TRUE = {"1", "true", "yes", "on"}


def _split(value: Optional[str]) -> tuple:
    return tuple(part.strip() for part in (value or "").split(",") if part.strip())


def _number(env: Mapping[str, str], name: str, default: float) -> float:
    raw = env.get(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        value = float(raw)
    except ValueError:
        raise ValueError(f"{name} must be a number, got {raw!r}") from None
    if value <= 0:
        raise ValueError(f"{name} must be greater than 0")
    return value


@dataclass(frozen=True)
class SecurityConfig:
    api_keys: frozenset = field(default_factory=frozenset)
    allow_unauthenticated: bool = False
    cors_origins: tuple = ()
    max_upload_bytes: int = 25 * 1024 * 1024
    max_body_bytes: int = 2 * 1024 * 1024
    subprocess_timeout: float = 120.0

    @classmethod
    def from_env(cls, env: Optional[Mapping[str, str]] = None) -> "SecurityConfig":
        env = os.environ if env is None else env
        keys = _split(env.get("EMPATHY_ENGINE_API_KEYS"))
        short = [k for k in keys if len(k) < MIN_KEY_LENGTH]
        if short:
            # Never echo the key itself.
            raise ValueError(
                f"EMPATHY_ENGINE_API_KEYS: {len(short)} key(s) shorter than {MIN_KEY_LENGTH} characters"
            )
        return cls(
            api_keys=frozenset(keys),
            allow_unauthenticated=env.get("EMPATHY_ENGINE_ALLOW_UNAUTHENTICATED", "").strip().lower() in _TRUE,
            cors_origins=_split(env.get("EMPATHY_ENGINE_CORS_ORIGINS")),
            max_upload_bytes=int(_number(env, "EMPATHY_ENGINE_MAX_UPLOAD_MB", 25) * 1024 * 1024),
            max_body_bytes=int(_number(env, "EMPATHY_ENGINE_MAX_BODY_MB", 2) * 1024 * 1024),
            subprocess_timeout=_number(env, "EMPATHY_ENGINE_SUBPROCESS_TIMEOUT", 120),
        )

    @property
    def auth_configured(self) -> bool:
        return bool(self.api_keys) or self.allow_unauthenticated


def presented_key(headers: Mapping[str, str]) -> Optional[str]:
    """Pull the client's key from `Authorization: Bearer ...` or `X-API-Key`."""
    auth = headers.get("authorization", "")
    scheme, _, token = auth.partition(" ")
    if scheme.lower() == "bearer" and token.strip():
        return token.strip()
    return headers.get("x-api-key") or None


def key_is_valid(config: SecurityConfig, key: Optional[str]) -> bool:
    if not key:
        return False
    # compare_digest takes the same time whether the first or last character
    # differs, so response timing can't be used to guess a key piece by piece.
    # Check every key (no early exit) for the same reason.
    matched = False
    for valid in config.api_keys:
        matched |= hmac.compare_digest(key.encode(), valid.encode())
    return matched


def safe_audio_suffix(filename: Optional[str], default: str = ".wav") -> str:
    """Return a whitelisted lowercase suffix for an uploaded file, or raise 415."""
    if not filename:
        return default
    _, dot, ext = filename.rpartition(".")
    suffix = f".{ext.lower()}" if dot else default
    if suffix not in ALLOWED_AUDIO_SUFFIXES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported audio type. Allowed: {', '.join(sorted(ALLOWED_AUDIO_SUFFIXES))}",
        )
    return suffix
