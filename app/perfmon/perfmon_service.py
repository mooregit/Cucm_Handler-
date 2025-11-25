from __future__ import annotations

from typing import Any, Dict, List

from app.perfmon.perfmon_client import PerfmonClient


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
    # PerfMon expects 'Object' elements in the request
    object_list = {
        "Object": [
            {
                "Name": _make_object_name(server, c),
            }
            for c in counters
        ]
    }

    res = perfmon.perfmonCollectCounterData(Objects=object_list)

    # Normalize output
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