# tests/axl/test_axl_client.py
import pytest

from app.axl.axl_client import AXLClient


class DummyZeepService:
    def __init__(self):
        self.calls = []

    def getPhone(self, **kwargs):
        self.calls.append(("getPhone", kwargs))
        return {"name": kwargs.get("name"), "description": "Test Phone"}

    def listPhone(self, **kwargs):
        self.calls.append(("listPhone", kwargs))
        return {"total": 10}


class DummyZeepClient:
    def __init__(self):
        self.service = DummyZeepService()


def test_axl_client_call_invokes_underlying_service(monkeypatch):
    """
    Verify that AXLClient.call('getPhone', ...) forwards to zeep.service.getPhone
    and returns the result.
    """
    dummy_zeep = DummyZeepClient()

    # Patch the internal builder used inside AXLClient
    import app.axl.axl_client as axl_module

    def fake_build_zeep_client(wsdl_path, host, username, password):
        assert wsdl_path == "/tmp/dummy.wsdl"
        assert host == "cucm.test.local"
        assert username == "testuser"
        assert password == "testpass"
        return dummy_zeep

    monkeypatch.setattr(axl_module, "_build_zeep_client", fake_build_zeep_client)

    client = AXLClient(
        wsdl_path="/tmp/dummy.wsdl",
        host="cucm.test.local",
        username="testuser",
        password="testpass",
    )

    result = client.call("getPhone", name="SEP1234567890")

    assert result == {"name": "SEP1234567890", "description": "Test Phone"}
    assert dummy_zeep.service.calls[0][0] == "getPhone"
    assert dummy_zeep.service.calls[0][1]["name"] == "SEP1234567890"


def test_axl_client_raises_for_unknown_method(monkeypatch):
    """
    If the SOAP service has no attribute for the given method_name,
    AXLClient.call should raise AttributeError.
    """
    dummy_zeep = DummyZeepClient()

    import app.axl.axl_client as axl_module

    monkeypatch.setattr(
        axl_module, "_build_zeep_client", lambda *args, **kwargs: dummy_zeep
    )

    client = AXLClient(
        wsdl_path="/tmp/dummy.wsdl",
        host="cucm.test.local",
        username="testuser",
        password="testpass",
    )

    with pytest.raises(AttributeError):
        client.call("nonExistentMethod", foo="bar")