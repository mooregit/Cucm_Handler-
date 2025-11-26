# tests/api/test_router_axl_raw.py
from fastapi.testclient import TestClient

from app.main import app
from app.axl.axl_service import AXLService
from tests.conftest import FakeAXLClient


def test_axl_status_endpoint(monkeypatch):
    """
    Test /axl/status (or whatever path you're using) by overriding the
    AXLService dependency and verifying the JSON response.
    """
    from app.api import router_axl_raw

    fake_client = FakeAXLClient()
    fake_client.responses["listPhone"] = {"total": 10}
    fake_client.responses["listUser"] = {"total": 20}
    fake_client.responses["listSipTrunk"] = {"total": 3}

    fake_service = AXLService(client=fake_client)

    def override_get_axl_service():
        return fake_service

    app.dependency_overrides[router_axl_raw.get_axl_service] = override_get_axl_service

    client = TestClient(app)
    resp = client.get("/axl/status")  # adjust path to your actual route

    assert resp.status_code == 200
    data = resp.json()

    # Adjust expected keys/shape to match your implementation
    assert data["devices"] == 10
    assert data["users"] == 20
    assert data["trunks"] == 3

    app.dependency_overrides.clear()


def test_axl_raw_call_passthrough(monkeypatch):
    """
    Example: if you have a POST /axl/raw endpoint that lets you specify a
    method and payload, this checks that it's calling the underlying service.
    """
    from app.api import router_axl_raw

    fake_client = FakeAXLClient()
    fake_client.responses["getPhone"] = {
        "name": "SEP1234567890",
        "description": "Test Phone",
    }

    fake_service = AXLService(client=fake_client)

    def override_get_axl_service():
        return fake_service

    app.dependency_overrides[router_axl_raw.get_axl_service] = override_get_axl_service

    client = TestClient(app)
    payload = {
        "method_name": "getPhone",
        "params": {"name": "SEP1234567890"},
    }

    resp = client.post("/axl/raw", json=payload)  # adjust path to your actual route

    assert resp.status_code == 200
    data = resp.json()

    # Expected response shape will depend on your router schema
    assert data["name"] == "SEP1234567890"
    assert data["description"] == "Test Phone"

    # Confirm the service actually called the underlying method
    assert fake_client.calls[0][0] == "getPhone"
    assert fake_client.calls[0][1]["name"] == "SEP1234567890"

    app.dependency_overrides.clear()