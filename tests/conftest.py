import atexit
import os
import shutil
import tempfile


def _configure_joblib_temp_dir() -> None:
    """Ensure joblib uses a writable temp dir during tests."""
    os.environ.setdefault("JOBLIB_MULTIPROCESSING", "0")
    if os.environ.get("JOBLIB_TEMP_FOLDER"):
        return
    path = tempfile.mkdtemp(prefix="empathy_engine_joblib_")
    os.environ["JOBLIB_TEMP_FOLDER"] = path
    atexit.register(shutil.rmtree, path, ignore_errors=True)


_configure_joblib_temp_dir()


import httpx
import pytest

from empathy_engine.api import server
from empathy_engine.api.security import SecurityConfig

TEST_KEY = "test-key-0123456789abcdef"


@pytest.fixture(autouse=True)
def secured_server(monkeypatch):
    """Every test runs against a server that requires TEST_KEY."""
    config = SecurityConfig(api_keys=frozenset({TEST_KEY}))
    monkeypatch.setattr(server, "security_config", config)
    return config


@pytest.fixture
def use_config(monkeypatch):
    """Swap in a different SecurityConfig for one test."""
    def _use(**kwargs):
        config = SecurityConfig(**{"api_keys": frozenset({TEST_KEY}), **kwargs})
        monkeypatch.setattr(server, "security_config", config)
        return config
    return _use


def make_client(key=TEST_KEY):
    headers = {"Authorization": f"Bearer {key}"} if key else {}
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=server.app),
                             base_url="http://test", headers=headers)


@pytest.fixture
def anyio_backend():
    return "asyncio"
