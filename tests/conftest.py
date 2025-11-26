# tests/conftest.py
import os
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.axl.axl_service import AXLService


@pytest.fixture(autouse=True)
def cucm_env(monkeypatch):
    """
    Ensure CUCM-related env vars are set to safe dummy values so that
    loaders / clients that depend on them do not fail.
    """
    monkeypatch.setenv("CUCM_HOST", "cucm.test.local")
    monkeypatch.setenv("CUCM_USERNAME", "testuser")
    monkeypatch.setenv("CUCM_PASSWORD", "testpass")
    monkeypatch.setenv("CUCM_WSDL_PATH", "/tmp/dummy.wsdl")
    yield


@pytest.fixture
def test_client():
    """
    FastAPI TestClient for API / router tests.
    """
    with TestClient(app) as client:
        yield client


class FakeAXLClient:
    """
    Simple fake AXL client that records calls and returns pre-configured results.
    """

    def __init__(self):
        # method_name -> value or Exception
        self.responses = {}
        self.calls = []

    def call(self, method_name: str, **kwargs):
        self.calls.append((method_name, kwargs))
        if method_name in self.responses:
            value = self.responses[method_name]
            if isinstance(value, Exception):
                raise value
            return value
        raise RuntimeError(f"Unexpected AXL method: {method_name}")


@pytest.fixture
def fake_axl_client():
    return FakeAXLClient()


@pytest.fixture
def axl_service(fake_axl_client):
    """
    AXLService wired to FakeAXLClient, used for unit tests
    (and can be injected into routers via dependency overrides).
    """
    return AXLService(client=fake_axl_client)