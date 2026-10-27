"""API hardening: keys, CORS, size limits, upload types, error hygiene, subprocess timeouts."""

import os

import httpx
import pytest
from fastapi.routing import APIRoute

from conftest import TEST_KEY, make_client
from empathy_engine.api import server
from empathy_engine.api.security import (
    PUBLIC_PATHS,
    SecurityConfig,
    key_is_valid,
    presented_key,
)

pytestmark = pytest.mark.anyio

TEXT = {"text": "I am okay"}


# --- API keys -----------------------------------------------------------------

async def test_missing_key_rejected():
    async with make_client(key=None) as client:
        r = await client.post("/analyze/text", json=TEXT)
    assert r.status_code == 401
    assert r.headers["www-authenticate"] == "Bearer"


async def test_wrong_key_rejected():
    async with make_client(key="wrong-key-0123456789abcdef") as client:
        r = await client.post("/analyze/text", json=TEXT)
    assert r.status_code == 401


async def test_bearer_key_accepted():
    async with make_client() as client:
        r = await client.post("/analyze/text", json=TEXT)
    assert r.status_code == 200


async def test_x_api_key_header_accepted():
    async with make_client(key=None) as client:
        r = await client.post("/analyze/text", json=TEXT, headers={"X-API-Key": TEST_KEY})
    assert r.status_code == 200


def test_every_configured_key_works():
    # Several keys, so whichever one a set iterates last, the others must still match.
    keys = {f"key-{i}-0123456789abcdef" for i in range(5)}
    config = SecurityConfig(api_keys=frozenset(keys))
    assert all(key_is_valid(config, key) for key in keys)


@pytest.mark.parametrize("path", ["/", "/health", "/openapi.json"])
async def test_public_paths_need_no_key(path):
    async with make_client(key=None) as client:
        r = await client.get(path)
    assert r.status_code == 200


def test_public_paths_are_exactly_the_expected_ones():
    # Pinned on purpose: making an endpoint public should be a visible, reviewed change.
    assert PUBLIC_PATHS == {"/", "/health", "/docs", "/docs/oauth2-redirect", "/redoc", "/openapi.json"}


async def test_every_other_endpoint_requires_a_key():
    # Fail-closed check: if someone adds an endpoint later, it's protected
    # without them having to remember anything.
    routes = [r for r in server.app.routes
              if isinstance(r, APIRoute) and r.path not in PUBLIC_PATHS]
    assert len(routes) > 20
    async with make_client(key=None) as client:
        for route in routes:
            method = sorted(route.methods)[0]
            r = await client.request(method, route.path, json={})
            assert r.status_code == 401, f"{method} {route.path} answered {r.status_code} without a key"


async def test_no_keys_configured_fails_closed(use_config):
    use_config(api_keys=frozenset())
    async with make_client() as client:
        r = await client.post("/analyze/text", json=TEXT)
        health = await client.get("/health")
    assert r.status_code == 503
    assert health.status_code == 200


async def test_allow_unauthenticated_for_local_dev(use_config):
    use_config(api_keys=frozenset(), allow_unauthenticated=True)
    async with make_client(key=None) as client:
        r = await client.post("/analyze/text", json=TEXT)
    assert r.status_code == 200


def test_presented_key_parsing():
    assert presented_key({"authorization": "Bearer abc"}) == "abc"
    assert presented_key({"authorization": "bearer  abc "}) == "abc"
    assert presented_key({"authorization": "Basic abc"}) is None
    assert presented_key({"x-api-key": "xyz"}) == "xyz"
    assert presented_key({}) is None


def test_key_is_valid_rejects_empty_and_prefixes():
    config = SecurityConfig(api_keys=frozenset({TEST_KEY}))
    assert key_is_valid(config, TEST_KEY)
    assert not key_is_valid(config, None)
    assert not key_is_valid(config, "")
    assert not key_is_valid(config, TEST_KEY[:-1])
    assert not key_is_valid(config, TEST_KEY + "x")


# --- Config from environment ----------------------------------------------------

def test_config_defaults():
    config = SecurityConfig.from_env({})
    assert config.api_keys == frozenset()
    assert not config.auth_configured
    assert config.cors_origins == ()
    assert config.max_upload_bytes == 25 * 1024 * 1024
    assert config.max_body_bytes == 2 * 1024 * 1024


def test_config_parses_lists_and_numbers():
    config = SecurityConfig.from_env({
        "EMPATHY_ENGINE_API_KEYS": " key-one-0123456789abc , key-two-0123456789abc ,",
        "EMPATHY_ENGINE_CORS_ORIGINS": "https://app.example.com",
        "EMPATHY_ENGINE_MAX_UPLOAD_MB": "5",
        "EMPATHY_ENGINE_SUBPROCESS_TIMEOUT": "30",
    })
    assert config.api_keys == {"key-one-0123456789abc", "key-two-0123456789abc"}
    assert config.cors_origins == ("https://app.example.com",)
    assert config.max_upload_bytes == 5 * 1024 * 1024
    assert config.subprocess_timeout == 30


def test_short_keys_rejected_without_echoing_them():
    with pytest.raises(ValueError) as exc:
        SecurityConfig.from_env({"EMPATHY_ENGINE_API_KEYS": "hunter2"})
    assert "hunter2" not in str(exc.value)


@pytest.mark.parametrize("value", ["abc", "0", "-5"])
def test_bad_limits_rejected(value):
    with pytest.raises(ValueError):
        SecurityConfig.from_env({"EMPATHY_ENGINE_MAX_UPLOAD_MB": value})


# --- CORS -----------------------------------------------------------------------

async def test_no_cors_headers_by_default():
    async with make_client() as client:
        r = await client.post("/analyze/text", json=TEXT, headers={"Origin": "https://evil.example"})
    assert r.status_code == 200
    assert "access-control-allow-origin" not in r.headers


# --- Size limits ----------------------------------------------------------------

async def test_oversized_json_body_rejected(use_config):
    use_config(max_body_bytes=1024)
    async with make_client() as client:
        r = await client.post("/analyze/text", json={"text": "x" * 2000})
    assert r.status_code == 413


async def test_streamed_body_without_length_rejected():
    async def body():
        yield b'{"text": "streamed"}'

    async with make_client() as client:
        r = await client.post("/analyze/text", content=body(),
                              headers={"Content-Type": "application/json"})
    assert r.status_code == 411


async def test_oversized_upload_rejected(use_config):
    use_config(max_upload_bytes=1024)
    async with make_client() as client:
        r = await client.post("/analyze/voice", files={"file": ("big.wav", b"\0" * 200_000)})
    assert r.status_code == 413


async def test_upload_limit_enforced_while_streaming(use_config, monkeypatch):
    # Even if the Content-Length check is bypassed, the copy loop stops at the limit.
    use_config(max_upload_bytes=1024)
    monkeypatch.setattr(server, "MULTIPART_OVERHEAD", 10_000_000)
    async with make_client() as client:
        r = await client.post("/analyze/voice", files={"file": ("big.wav", b"\0" * 5000)})
    assert r.status_code == 413


# --- Upload types and temp files ---------------------------------------------------

@pytest.mark.parametrize("name", ["evil.sh", "x.m3u8", "x.wav --output /etc/passwd"])
async def test_unsupported_upload_types_rejected(name):
    async with make_client() as client:
        r = await client.post("/analyze/multimodal", files={"file": (name, b"data")})
    assert r.status_code == 415


async def test_temp_upload_deleted_after_failure(monkeypatch):
    seen = []

    def boom(path):
        seen.append(path)
        raise RuntimeError("analysis exploded")

    monkeypatch.setattr(server.engine, "analyze_voice", boom)
    async with make_client() as client:
        r = await client.post("/analyze/voice", files={"file": ("clip.wav", b"RIFF")})
    assert r.status_code == 500
    assert seen and not os.path.exists(seen[0])


async def test_multimodal_temp_files_deleted(monkeypatch):
    seen = []
    real_analyze = server.engine.analyze

    def spy(text=None, audio_path=None, **kwargs):
        seen.append(audio_path)
        return real_analyze(text=text, audio_path=None, **kwargs)

    monkeypatch.setattr(server.engine, "analyze", spy)
    async with make_client() as client:
        r = await client.post("/analyze/multimodal", data={"text": "hello"},
                              files={"file": ("clip.wav", b"RIFF")})
    assert r.status_code == 200
    assert seen and seen[0] and not os.path.exists(seen[0])


# --- Error hygiene ----------------------------------------------------------------

async def test_internal_errors_do_not_leak_details(monkeypatch):
    def boom(**kwargs):
        raise RuntimeError("/home/someone/secret/path: user said 'I am okay'")

    monkeypatch.setattr(server.engine, "analyze_text", boom)
    async with make_client() as client:
        r = await client.post("/analyze/text", json=TEXT)
    assert r.status_code == 500
    assert "secret" not in r.text and "I am okay" not in r.text


# --- Subprocesses -------------------------------------------------------------------

def test_stt_command_is_killed_after_timeout(use_config, monkeypatch, tmp_path):
    use_config(subprocess_timeout=0.5)
    monkeypatch.setattr(server.settings, "stt_command", "sleep 10")
    import time
    start = time.monotonic()
    assert server._run_stt(str(tmp_path / "a.wav")) is None
    assert time.monotonic() - start < 5


def test_stt_failure_logs_never_include_transcript(use_config, monkeypatch, tmp_path):
    logged = []
    monkeypatch.setattr(server.logger, "error", lambda msg, *a, **k: logged.append(msg))
    # The command prints "secretwords" (reversed in the command text, because
    # the command itself is logged on purpose; its output must not be).
    monkeypatch.setattr(server.settings, "stt_command",
                        "sh -c 'echo sdrowterces | rev; exit 3'")
    assert server._run_stt(str(tmp_path / "a.wav")) is None
    assert logged and not any("secretwords" in m for m in logged)


# --- Startup checks (main) ------------------------------------------------------------

def test_local_mode_refuses_non_loopback_host(use_config, monkeypatch):
    use_config(api_keys=frozenset(), allow_unauthenticated=True)
    monkeypatch.setenv("HOST", "0.0.0.0")
    started = []
    monkeypatch.setattr(server.EmpathyAPI, "run", lambda self, **kw: started.append(kw))
    with pytest.raises(SystemExit) as exc:
        server.main()
    assert "HOST=0.0.0.0" in str(exc.value)
    assert started == []


def test_local_mode_starts_on_loopback(use_config, monkeypatch):
    use_config(api_keys=frozenset(), allow_unauthenticated=True)
    monkeypatch.delenv("HOST", raising=False)
    started = []
    monkeypatch.setattr(server.EmpathyAPI, "run", lambda self, **kw: started.append(kw))
    server.main()
    assert started == [{"host": "127.0.0.1", "port": 8000}]


def test_no_keys_refuses_to_start(use_config, monkeypatch):
    use_config(api_keys=frozenset())
    monkeypatch.setattr(server.EmpathyAPI, "run", lambda self, **kw: None)
    with pytest.raises(SystemExit):
        server.main()
