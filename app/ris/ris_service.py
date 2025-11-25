from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.ris.ris_client import RISClient


def _standard_device_search_criteria(
    dn_pattern: str = "%",
    device_class: str = "Phone",
    device_name_pattern: str = "%",
) -> Dict[str, Any]:
    """
    Build a common SelectCmDevice searchCriteria structure.

    RIS expects very specific IN parameters.
    """

    # See RIS WSDL docs for full type; this is a sane default.
    return {
        "MaxReturnedDevices": 1000,
        "Class": device_class,
        "Model": 255,   # 255 = Any model
        "Status": "Any",
        "NodeName": "",
        "SelectBy": "Name",
        "SelectItems": {
            "SelectItem": [
                {
                    "Item": device_name_pattern,
                }
            ]
        },
        "Protocol": "Any",
        "DownloadStatus": "Any",
    }


def get_registered_devices(
    ris: RISClient,
    device_name_pattern: str = "%",
    device_class: str = "Phone",
    max_devices: int = 1000,
) -> List[Dict[str, Any]]:
    """
    Uses SelectCmDevice to get real-time info about devices that match the pattern.

    Returns a list of devices with registration status, IP, etc.
    """

    state_info = ""  # empty for initial query

    criteria = _standard_device_search_criteria(
        device_class=device_class,
        device_name_pattern=device_name_pattern,
    )
    criteria["MaxReturnedDevices"] = max_devices

    # RIS SelectCmDevice request envelope
    res = ris.SelectCmDevice(
        StateInfo=state_info,
        CmSelectionCriteria=criteria,
    )

    result = []
    if not res or "SelectCmDeviceResult" not in res:
        return result

    outer = res["SelectCmDeviceResult"]
    nodes = (outer.get("CmNodes") or {}).get("CmNode", []) or []

    for node in nodes:
        devs = (node.get("CmDevices") or {}).get("CmDevice", []) or []
        for d in devs:
            result.append(d)

    return result


def get_registered_phones(ris: RISClient, pattern: str = "SEP%") -> List[Dict[str, Any]]:
    """
    Convenience wrapper for phone-class devices whose name starts with 'SEP'.
    """
    return get_registered_devices(
        ris=ris,
        device_name_pattern=pattern,
        device_class="Phone",
    )


def get_registered_trunks(ris: RISClient, pattern: str = "%") -> List[Dict[str, Any]]:
    """
    Treat trunks as 'Gateway' class for RIS purposes.
    Device names will typically match the trunk/gateway name in CUCM.
    """
    return get_registered_devices(
        ris=ris,
        device_name_pattern=pattern,
        device_class="Gateway",
    )


def count_registered_devices(ris: RISClient, device_class: str = "Phone") -> int:
    """
    Returns the count of devices RIS reports for the given class.
    """
    devices = get_registered_devices(ris=ris, device_name_pattern="%", device_class=device_class)
    return len(devices)


def get_trunk_status_summary(
    ris: RISClient,
    pattern: str = "%",
) -> Dict[str, Any]:
    """
    Very high-level trunk summary based on RIS registration.

    Note: This tells you registration (Up/Down/Unknown-ish) but not
    detailed call path performance.
    """

    trunks = get_registered_trunks(ris, pattern=pattern)
    up = 0
    down = 0
    unknown = 0

    for t in trunks:
        status = t.get("Status") or ""
        if status.lower() == "registered":
            up += 1
        elif status.lower() in {"unregistered", "rejected", "unknown"}:
            down += 1
        else:
            unknown += 1

    return {
        "pattern": pattern,
        "total": len(trunks),
        "up": up,
        "down": down,
        "unknown": unknown,
        "trunks": trunks,
    }