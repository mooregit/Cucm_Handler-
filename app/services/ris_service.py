from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.ris.ris_client import RISClient


# =============================================================================
# LOW-LEVEL HELPER FUNCTIONS (your existing code)
# =============================================================================


def _standard_device_search_criteria(
    dn_pattern: str = "%",
    device_class: str = "Phone",
    device_name_pattern: str = "%",
) -> Dict[str, Any]:
    """
    Build a common SelectCmDevice searchCriteria structure.

    RIS expects very specific IN parameters.
    """
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

    res = ris.SelectCmDevice(
        StateInfo=state_info,
        CmSelectionCriteria=criteria,
    )

    result: List[Dict[str, Any]] = []
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
    devices = get_registered_devices(
        ris=ris,
        device_name_pattern="%",
        device_class=device_class,
    )
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
        status = (t.get("Status") or "").lower()
        if status == "registered":
            up += 1
        elif status in {"unregistered", "rejected", "unknown"}:
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


# =============================================================================
# RISService CLASS WRAPPER
# =============================================================================

import asyncio
import time


class RISService:
    """
    High-level wrapper exposing RIS operations as methods.
    FastAPI expects this when using `Depends(get_ris_service)`.
    """

    def __init__(self, client: Optional[RISClient] = None) -> None:
        self.client = client

    def _require_client(self) -> RISClient:
        if self.client is None:
            raise RuntimeError(
                "RISClient is not configured. "
                "Wire a real RISClient into get_ris_service() to enable live RIS calls."
            )
        return self.client

    # -------------------------
    # Core device queries
    # -------------------------

    async def get_registered_devices(
        self,
        device_name_pattern: str = "%",
        device_class: str = "Phone",
        max_devices: int = 1000,
    ) -> List[Dict[str, Any]]:
        client = self._require_client()
        return await asyncio.to_thread(
            get_registered_devices,
            client,
            device_name_pattern,
            device_class,
            max_devices,
        )

    async def get_registered_phones(
        self,
        pattern: str = "SEP%",
    ) -> List[Dict[str, Any]]:
        client = self._require_client()
        return await asyncio.to_thread(
            get_registered_phones,
            client,
            pattern,
        )

    async def get_registered_trunks(
        self,
        pattern: str = "%",
    ) -> List[Dict[str, Any]]:
        client = self._require_client()
        return await asyncio.to_thread(
            get_registered_trunks,
            client,
            pattern,
        )

    async def count_registered_devices(
        self,
        device_class: str = "Phone",
    ) -> int:
        client = self._require_client()
        return await asyncio.to_thread(
            count_registered_devices,
            client,
            device_class,
        )

    # -------------------------
    # Higher-level helpers used by routers
    # -------------------------

    async def list_registered_devices(
        self,
        cucm_node: Optional[str] = None,
        device_class: Optional[str] = "Phone",
        limit: int = 1000,
    ) -> List[Dict[str, Any]]:
        """
        Used by /devices/registered in the router.
        """
        devices = await self.get_registered_devices(
            device_name_pattern="%",
            device_class=device_class or "Phone",
            max_devices=limit,
        )

        if cucm_node:
            node_lower = cucm_node.lower()
            devices = [
                d
                for d in devices
                if (d.get("NodeName") or "").lower() == node_lower
            ]

        return devices[:limit]

    async def get_device_status(self, device_name: str) -> Optional[Dict[str, Any]]:
        """
        Used by /devices/{device_name}/status.
        """
        devices = await self.get_registered_devices(
            device_name_pattern=device_name,
            device_class="Any",
            max_devices=10,
        )
        return devices[0] if devices else None

    async def get_registered_statistics(self) -> Dict[str, Any]:
        """
        Used by /devices/summary for real RIS stats.
        """
        phones = await self.get_registered_devices(
            device_name_pattern="%",
            device_class="Phone",
            max_devices=100000,
        )
        trunks = await self.get_registered_devices(
            device_name_pattern="%",
            device_class="Gateway",
            max_devices=100000,
        )

        return {
            "total_registered_phones": len(phones),
            "total_registered_trunks": len(trunks),
        }

    async def get_trunk_status_summary(self, pattern: str = "%") -> Dict[str, Any]:
        client = self._require_client()
        return await asyncio.to_thread(
            get_trunk_status_summary,
            client,
            pattern,
        )

    # -------------------------
    # Health / readiness
    # -------------------------

    async def health_check(self) -> Dict[str, Any]:
        """
        Lightweight RIS health check used by /health and /health/ris.
        """
        start = time.perf_counter()
        try:
            # Just try to fetch a single phone device as a probe.
            _ = await self.get_registered_devices(
                device_name_pattern="%",
                device_class="Phone",
                max_devices=1,
            )
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            return {
                "ok": True,
                "response_time_ms": elapsed_ms,
            }
        except Exception as exc:
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            return {
                "ok": False,
                "response_time_ms": elapsed_ms,
                "error": str(exc),
            }


# =============================================================================
# FastAPI dependency
# =============================================================================

def get_ris_service() -> RISService:
    """
    FastAPI dependency that returns an initialized RISService.

    Currently returns RISService with no underlying RISClient configured.
    This is intentional so that your mock-mode routers work without a live
    CUCM RIS endpoint.

    When you are ready to wire a real RISClient, replace this with something
    like:

        from app.ris.ris_loader import get_ris_client
        client = get_ris_client()
        return RISService(client)

    For now, routes that rely on RISService in *non-mock* mode will raise
    a RuntimeError until a real client is wired.
    """
    return RISService(client=None)
