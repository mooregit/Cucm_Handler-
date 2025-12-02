# app/api/router_status.py

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException

from app.core.axl_loader import get_axl_client
from app.core.ris_loader import get_ris_client
from app.core.perfmon_loader import get_perfmon_client

from app.axl.axl_client import AXLClient
from app.ris.ris_client import RISClient
from app.perfmon.perfmon_client import PerfmonClient

from app.services.axl_service import (
    get_system_summary,
    get_process_nodes,
)
from app.services.ris_service import (
    get_registered_phones,
    get_registered_trunks,
    count_registered_devices,
    get_trunk_status_summary,
)
from app.services.perfmon_service import (
    get_cluster_health_summary,
)

router = APIRouter(prefix="/status", tags=["Cluster Status"])


def _extract_server_names_from_nodes(nodes: List[Dict[str, Any]]) -> List[str]:
    """
    Extract server names from AXL processnode rows.

    Typically 'name' field contains the node name used by PerfMon, e.g. 'cucm-pub'.
    """
    servers: List[str] = []
    for n in nodes:
        name = n.get("name")
        if name:
            servers.append(name)
    return servers


@router.get(
    "/cluster",
    summary="Cluster-wide status summary",
    description=(
        "Returns a combined view of CUCM cluster status:\n"
        "- AXL configuration summary (version, counts, nodes)\n"
        "- RISPort real-time device and trunk status\n"
        "- PerfMon node health metrics (CPU, memory, DB counters)"
    ),
)
def get_cluster_status(
    axl: AXLClient = Depends(get_axl_client),
    ris: RISClient = Depends(get_ris_client),
    perfmon: PerfmonClient = Depends(get_perfmon_client),
) -> Dict[str, Any]:
    try:
        # ---------------------------------------------------------------------
        # AXL: configuration-level summary
        # ---------------------------------------------------------------------
        config_summary = get_system_summary(axl)
        nodes = config_summary.get("processNodes", []) or []
        servers = _extract_server_names_from_nodes(nodes)

        # ---------------------------------------------------------------------
        # RIS: real-time device and trunk info
        # ---------------------------------------------------------------------
        registered_phones = get_registered_phones(ris, pattern="SEP%")
        registered_trunks = get_registered_trunks(ris, pattern="%")

        phone_registered_count = len(registered_phones)
        trunk_registered_summary = get_trunk_status_summary(ris, pattern="%")

        # Optional: total phones (registered vs total) by class
        phone_total = count_registered_devices(ris, device_class="Phone")
        gateway_total = count_registered_devices(ris, device_class="Gateway")

        # ---------------------------------------------------------------------
        # PerfMon: node health metrics
        # ---------------------------------------------------------------------
        perf_summary = {}
        if servers:
            perf_summary = get_cluster_health_summary(perfmon, servers=servers)

        return {
            "axlConfig": config_summary,
            "risRealtime": {
                "phones": {
                    "registeredCount": phone_registered_count,
                    "totalClassCount": phone_total,
                    "sample": registered_phones[:50],  # limit payload
                },
                "trunks": {
                    "summary": trunk_registered_summary,
                    "totalGatewayClassCount": gateway_total,
                },
            },
            "perfmon": perf_summary,
        }

    except HTTPException:
        # Let HTTPExceptions bubble up unchanged
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to collect cluster status: {exc}")


@router.get(
    "/nodes",
    summary="List CUCM process nodes",
    description="Returns the CUCM nodes (publisher and subscribers) from AXL.",
)
def list_nodes(
    axl: AXLClient = Depends(get_axl_client),
) -> Dict[str, Any]:
    try:
        nodes = get_process_nodes(axl)
        return {"nodes": nodes}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to list nodes: {exc}")


@router.get(
    "/devices",
    summary="Real-time device status summary",
    description=(
        "Returns a real-time summary of registered phones and gateways "
        "from RISPort."
    ),
)
def devices_status(
    ris: RISClient = Depends(get_ris_client),
) -> Dict[str, Any]:
    try:
        phones = get_registered_phones(ris, pattern="SEP%")
        trunks = get_registered_trunks(ris, pattern="%")

        return {
            "phones": {
                "registeredCount": len(phones),
                "sample": phones[:100],
            },
            "trunks": {
                "registeredCount": len(trunks),
                "sample": trunks[:100],
            },
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to collect device status: {exc}")


@router.get(
    "/perfmon",
    summary="PerfMon node health summary",
    description="Returns PerfMon CPU/memory/DB counters for each supplied node.",
)
def perfmon_status(
    axl: AXLClient = Depends(get_axl_client),
    perfmon: PerfmonClient = Depends(get_perfmon_client),
) -> Dict[str, Any]:
    try:
        nodes = get_process_nodes(axl)
        servers = _extract_server_names_from_nodes(nodes)
        summary = get_cluster_health_summary(perfmon, servers=servers)
        return summary
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to collect PerfMon status: {exc}")