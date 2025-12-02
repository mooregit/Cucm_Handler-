# app/api/routers/perfmon_raw.py

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.services.perfmon_service import PerfMonService, get_perfmon_service


router = APIRouter(
    prefix="/perfmon",
    tags=["PerfMon (raw)"],
)


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class CollectCountersRequest(BaseModel):
    """
    Request body for collecting specific PerfMon counters from a node.
    """

    server: str = Field(
        ...,
        description="CUCM node / server name (e.g. cucm-pub).",
    )
    counters: List[str] = Field(
        ...,
        description=(
            "List of PerfMon counter paths after server name, "
            'e.g. ["Cisco Unified CallManager\\\\CPU Usage"].'
        ),
    )


class ClusterHealthRequest(BaseModel):
    """
    Request body for a simple cluster health summary.
    """

    servers: List[str] = Field(
        ...,
        description="List of CUCM nodes to sample (e.g. ['cucm-pub', 'cucm-sub1']).",
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/health",
    summary="PerfMon service health check",
    response_description="Basic health status from PerfMonService.",
)
async def perfmon_health(
    perfmon: PerfMonService = Depends(get_perfmon_service),
) -> Dict[str, Any]:
    """
    Lightweight health probe – uses PerfMonService.health_check().
    """
    try:
        return await perfmon.health_check()
    except RuntimeError as exc:
        # Typically indicates PerfmonClient is not configured.
        raise HTTPException(status_code=503, detail=str(exc))


@router.post(
    "/collect",
    summary="Collect raw PerfMon counters",
    response_description="Key/value map of requested counters.",
)
async def perfmon_collect(
    payload: CollectCountersRequest,
    perfmon: PerfMonService = Depends(get_perfmon_service),
) -> Dict[str, Any]:
    """
    Collect raw PerfMon counters for a single node.

    Example body:

        {
          "server": "cucm-pub",
          "counters": [
            "Cisco Unified CallManager\\\\CPU Usage",
            "Memory\\\\% Committed Bytes In Use"
          ]
        }
    """
    try:
        data = await perfmon.collect_counters(
            server=payload.server,
            counters=payload.counters,
        )
        return {"server": payload.server, "counters": data}
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"PerfMon collect failed: {exc}")


@router.post(
    "/node-health",
    summary="Get basic node health (PerfMon)",
    response_description="CPU/memory/DB-related counters for a node.",
)
async def perfmon_node_health(
    payload: CollectCountersRequest,
    perfmon: PerfMonService = Depends(get_perfmon_service),
) -> Dict[str, Any]:
    """
    Convenience endpoint over PerfMonService.get_basic_node_health().

    Ignores the `counters` field from the request; uses the default health
    counter set defined in PerfMonService.
    """
    try:
        data = await perfmon.get_basic_node_health(server=payload.server)
        return data
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"PerfMon node-health failed: {exc}")


@router.post(
    "/cluster-health",
    summary="Get cluster health summary (PerfMon)",
    response_description="Basic health metrics for multiple nodes.",
)
async def perfmon_cluster_health(
    payload: ClusterHealthRequest,
    perfmon: PerfMonService = Depends(get_perfmon_service),
) -> Dict[str, Any]:
    """
    Roll-up health information for multiple CUCM nodes.

    Uses the same basic counters as /node-health for each server in the list.
    """
    try:
        data = await perfmon.get_cluster_health_summary(servers=payload.servers)
        return data
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"PerfMon cluster-health failed: {exc}")
