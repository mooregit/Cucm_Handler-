from __future__ import annotations

from typing import Any, Dict, List, Optional
import asyncio
import time

from app.perfmon.perfmon_client import PerfmonClient


# =============================================================================
# LOW-LEVEL HELPER FUNCTIONS (your existing code)
# =============================================================================


def _make_object_name(server: str, counter: str) -> str:
    """
    Build a PerfMon object name.

    Example counter strings (check Cisco docs / RTMT):
      - "Cisco Unified CallManager\\CPU Usage"
      - "Cisco DB\\DB Connections"
      - "System\\Processor Queue Length"
    """
    return f"\\{server}\\{counter}"


def collect_counters(
    perfmon: PerfmonClient,
    server: str,
    counters: List[str],
) -> Dict[str, Any]:
    """
    Generic wrapper for perfmonCollectCounterData.

    :param server: CUCM node name (same as processnode.name)
    :param counters: List of counter paths after server name:
                     e.g. ["Cisco Unified CallManager\\CPU Usage"].
    """
    object_list = {
        "Object": [
            {
                "Name": _make_object_name(server, c),
            }
            for c in counters
        ]
    }

    res = perfmon.perfmonCollectCounterData(Objects=object_list)

    result: Dict[str, Any] = {}
    if not res or "perfmonCollectCounterDataResult" not in res:
        return result

    outer = res["perfmonCollectCounterDataResult"]
    obj_array = (outer.get("ArrayOfCounterInfo") or {}).get("CounterInfo", []) or []

    for item in obj_array:
        name = item.get("Name")
        value = item.get("Value")
        if name:
            result[name] = value

    return result


def get_basic_node_health(
    perfmon: PerfmonClient,
    server: str,
) -> Dict[str, Any]:
    """
    Collect basic CPU, memory, and DB health metrics for a given node.
    Exact counter names vary by CUCM version; adjust as needed.
    """
    counters = [
        "Cisco Unified CallManager\\CPU Usage",
        "Cisco DB\\Active DB Connections",
        "Cisco DB\\Total DB Connections",
        "System\\Processor Queue Length",
        "Memory\\% Committed Bytes In Use",
    ]

    data = collect_counters(perfmon, server, counters)

    return {
        "server": server,
        "counters": data,
    }


def get_cluster_health_summary(
    perfmon: PerfmonClient,
    servers: List[str],
) -> Dict[str, Any]:
    """
    Quick cluster-level rollup of node health using PerfMon counters.
    """
    nodes = []
    for s in servers:
        nodes.append(get_basic_node_health(perfmon, s))

    return {
        "nodes": nodes,
    }


# =============================================================================
# PerfMonService CLASS WRAPPER
# =============================================================================


class PerfMonService:
    """
    High-level wrapper exposing PerfMon operations as methods.
    FastAPI expects this when using `Depends(get_perfmon_service)`.
    """

    def __init__(self, client: Optional[PerfmonClient] = None) -> None:
        self.client = client

    def _require_client(self) -> PerfmonClient:
        if self.client is None:
            raise RuntimeError(
                "PerfmonClient is not configured. "
                "Wire a real PerfmonClient into get_perfmon_service() "
                "to enable live PerfMon calls."
            )
        return self.client

    # -------------------------
    # Core counters
    # -------------------------

    async def collect_counters(
        self,
        server: str,
        counters: List[str],
    ) -> Dict[str, Any]:
        client = self._require_client()
        return await asyncio.to_thread(
            collect_counters,
            client,
            server,
            counters,
        )

    async def get_basic_node_health(self, server: str) -> Dict[str, Any]:
        client = self._require_client()
        return await asyncio.to_thread(
            get_basic_node_health,
            client,
            server,
        )

    async def get_cluster_health_summary(
        self,
        servers: List[str],
    ) -> Dict[str, Any]:
        client = self._require_client()
        return await asyncio.to_thread(
            get_cluster_health_summary,
            client,
            servers,
        )

    # -------------------------
    # Health / readiness
    # -------------------------

    async def health_check(self) -> Dict[str, Any]:
        """
        Lightweight PerfMon health check used by /health and /health/perfmon.
        """
        start = time.perf_counter()
        try:
            # Probe: try collecting a harmless counter from a dummy server name.
            # In a real implementation you might pass a real node here or
            # use a dedicated lightweight endpoint.
            # If client is not configured, _require_client() will raise.
            _ = await self.collect_counters(
                server="dummy",
                counters=["System\\Processor Queue Length"],
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


def get_perfmon_service() -> PerfMonService:
    """
    FastAPI dependency that returns an initialized PerfMonService.

    Currently returns PerfMonService with no underlying PerfmonClient configured.
    This is fine while you are in MOCK health/devices mode.

    When you are ready to use real PerfMon, change this to:

        from app.perfmon.perfmon_loader import get_perfmon_client
        client = get_perfmon_client()
        return PerfMonService(client)
    """
    return PerfMonService(client=None)
