# tests/axl/test_axl_service.py
from app.axl.axl_service import AXLService


def test_get_device_count_uses_listPhone(fake_axl_client):
    fake_axl_client.responses["listPhone"] = {"total": 42}

    service = AXLService(client=fake_axl_client)
    count = service.get_device_count()

    assert count == 42
    assert fake_axl_client.calls[0][0] == "listPhone"


def test_get_user_count_uses_listUser(fake_axl_client):
    fake_axl_client.responses["listUser"] = {"total": 7}

    service = AXLService(client=fake_axl_client)
    count = service.get_user_count()

    assert count == 7
    assert fake_axl_client.calls[0][0] == "listUser"


def test_get_trunk_count_uses_listSipTrunk(fake_axl_client):
    fake_axl_client.responses["listSipTrunk"] = {"total": 5}

    service = AXLService(client=fake_axl_client)
    count = service.get_trunk_count()

    assert count == 5
    assert fake_axl_client.calls[0][0] == "listSipTrunk"


def test_get_cluster_status_aggregates(fake_axl_client):
    """
    Whatever your shape is, validate combined status.
    """
    fake_axl_client.responses["listPhone"] = {"total": 10}
    fake_axl_client.responses["listUser"] = {"total": 20}
    fake_axl_client.responses["listSipTrunk"] = {"total": 3}

    service = AXLService(client=fake_axl_client)

    # If your method name is different, adjust here:
    status = service.get_cluster_status()

    assert status["devices"] == 10
    assert status["users"] == 20
    assert status["trunks"] == 3