import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, status, HTTPException

from app.services.axl_service import AXLService, get_axl_service
from app.services.ris_service import RISService, get_ris_service
from app.services.server_health_service import ServerHealthService, get_server_health_service
from app.services.perfmon_service import (
    PerfMonService,
    get_perfmon_service,
)

router = APIRouter(
    prefix="/health",
    tags=["Health"],
)

# -------------------------------------------------------------------
# Mock mode toggle
# -------------------------------------------------------------------
# Set USE_MOCK_HEALTH=false in the environment to use real health services.
USE_MOCK_HEALTH = os.getenv("USE_MOCK_HEALTH", "true").lower() == "true"

# -------------------------------------------------------------------
# Mock test data
# -------------------------------------------------------------------

MOCK_SERVERS: List[Dict[str, Any]] = [
    {
        "id": 1,
        "name": "cucm-pub",
        "role": "CUCM Publisher",
        "hostname": "cucm-pub.lab.local",
        "ip_address": "10.10.10.10",
        "cluster": "Cluster-A",
        "status": "Healthy",
        "services": {
            "Cisco CallManager": "Running",
            "Cisco Tftp": "Running",
            "Cisco AXL Web Service": "Running",
        },
        "metrics": {
            "cpu_usage_percent": 21.5,
            "memory_usage_percent": 63.2,
            "disk_usage_percent": 54.0,
        },
        "last_checked": "2025-01-01T12:00:00Z",
    },
    {
        "id": 2,
        "name": "cucm-sub1",
        "role": "CUCM Subscriber",
        "hostname": "cucm-sub1.lab.local",
        "ip_address": "10.10.10.11",
        "cluster": "Cluster-A",
        "status": "Degraded",
        "services": {
            "Cisco CallManager": "Running",
            "Cisco Tftp": "Stopped",
            "Cisco AXL Web Service": "Running",
        },
        "metrics": {
            "cpu_usage_percent": 48.3,
            "memory_usage_percent": 72.9,
            "disk_usage_percent": 70.1,
        },
        "last_checked": "2025-01-01T12:00:00Z",
    },
    {
        "id": 3,
        "name": "cucx-ucxn",
        "role": "Unity Connection",
        "hostname": "cucx-ucxn.lab.local",
        "ip_address": "10.10.10.20",
        "cluster": "Cluster-A",
        "status": "Healthy",
        "services": {
            "Connection Conversation Manager": "Running",
            "Connection Message Transfer Agent": "Running",
        },
        "metrics": {
            "cpu_usage_percent": 18.1,
            "memory_usage_percent": 59.0,
            "disk_usage_percent": 40.7,
        },
        "last_checked": "2025-01-01T12:00:00Z",
    },
]

MOCK_AXL_STATUS: Dict[str, Any] = {
    "ok": True,
    "response_time_ms": 42,
    "cucm_version": "14.0(1)",
    "last_successful_check": "2025-01-01T12:00:00Z",
    "details": "Mock AXL connection to cucm-pub.lab.local successful.",
}

MOCK_RIS_STATUS: Dict[str, Any] = {
    "ok": True,
    "response_time_ms": 65,
    "nodes_checked": ["cucm-pub", "cucm-sub1"],
    "registered_devices": 2,
    "unregistered_devices": 1,
    "last_successful_check": "2025-01-01T12:00:00Z",
}

MOCK_PERFMON_STATUS: Dict[str, Any] = {
    "ok": True,
    "response_time_ms": 55,
    "counters_sampled": [
        "System/CPUUtilization",
        "System/MemoryUsed",
        "System/DiskUsage",
    ],
    "last_successful_check": "2025-01-01T12:00:00Z",
}


def _get_mock_server_by_id(server_id: int) -> Optional[Dict[str, Any]]:
    return next((s for s in MOCK_SERVERS if s["id"] == server_id), None)


# -------------------------------------------------------------------
# Endpoints
# -------------------------------------------------------------------


@router.get("/servers", summary="Health for all UC servers")
async def servers_health(
    server_health: ServerHealthService = Depends(get_server_health_service),
):
    if USE_MOCK_HEALTH:
        # In mock mode, just return the static list
        return MOCK_SERVERS

    return await server_health.get_all_servers_health()


@router.get("/servers/{server_id}", summary="Health for a specific server")
async def server_health(
    server_id: int,
    server_health: ServerHealthService = Depends(get_server_health_service),
):
    if USE_MOCK_HEALTH:
        data = _get_mock_server_by_id(server_id)
        if not data:
            raise HTTPException(status_code=404, detail="Server not found")
        return data

    data = await server_health.get_server_health(server_id)
    if not data:
        raise HTTPException(status_code=404, detail="Server not found")
    return data


@router.get(
    "",
    summary="Overall health summary",
    response_description="Aggregated health status for the service and CUCM subsystems.",
)
async def health_root(
    axl: AXLService = Depends(get_axl_service),
    ris: RISService = Depends(get_ris_service),
    perfmon: PerfMonService = Depends(get_perfmon_service),
) -> Dict[str, Any]:
    """
    Aggregate health information for:
    - API service itself
    - AXL connectivity
    - RISPort connectivity
    - PerfMon connectivity
    - Optional high-level CUCM cluster indicators
    """
    if USE_MOCK_HEALTH:
        overall_ok = all(
            [
                MOCK_AXL_STATUS.get("ok", False),
                MOCK_RIS_STATUS.get("ok", False),
                MOCK_PERFMON_STATUS.get("ok", False),
            ]
        )
        return {
            "service": {
                "ok": True,
                "environment": "mock",
            },
            "axl": MOCK_AXL_STATUS,
            "ris": MOCK_RIS_STATUS,
            "perfmon": MOCK_PERFMON_STATUS,
            "overall_ok": overall_ok,
        }

    axl_status = await axl.health_check()
    ris_status = await ris.health_check()
    perfmon_status = await perfmon.health_check()

    overall_ok = all(
        [
            axl_status.get("ok", False),
            ris_status.get("ok", False),
            perfmon_status.get("ok", False),
        ]
    )

    return {
        "service": {
            "ok": True,
        },
        "axl": axl_status,
        "ris": ris_status,
        "perfmon": perfmon_status,
        "overall_ok": overall_ok,
    }


@router.get(
    "/live",
    summary="Liveness probe",
    response_description="Simple liveness indicator for the API container.",
)
async def liveness() -> Dict[str, bool]:
    """
    Basic liveness endpoint for container orchestrators (Kubernetes, etc.).
    Does not perform external calls; just indicates the process is up.
    """
    # Liveness is the same in both real and mock modes
    return {"ok": True}


@router.get(
    "/ready",
    summary="Readiness probe",
    response_description="Readiness indicator including basic dependency checks.",
)
async def readiness(
    axl: AXLService = Depends(get_axl_service),
) -> Dict[str, Any]:
    """
    Readiness check that verifies the API is ready to serve traffic.
    Usually includes at least one dependency (AXL) to catch initialization issues.
    """
    if USE_MOCK_HEALTH:
        ready = MOCK_AXL_STATUS.get("ok", False)
        return {
            "ok": ready,
            "axl": MOCK_AXL_STATUS,
        }

    axl_status = await axl.health_check()
    ready = axl_status.get("ok", False)
    return {
        "ok": ready,
        "axl": axl_status,
    }


@router.get(
    "/axl",
    summary="AXL health",
    response_description="Health status for AXL connectivity.",
)
async def axl_health(
    axl: AXLService = Depends(get_axl_service),
) -> Dict[str, Any]:
    """
    Detailed health information about AXL connectivity, such as:
    - ok: bool
    - response_time_ms
    - cucm_version
    - last_successful_check
    """
    if USE_MOCK_HEALTH:
        return MOCK_AXL_STATUS

    return await axl.health_check()


@router.get(
    "/ris",
    summary="RISPort health",
    response_description="Health status for RISPort connectivity.",
)
async def ris_health(
    ris: RISService = Depends(get_ris_service),
) -> Dict[str, Any]:
    """
    Detailed health information about RISPort connectivity, such as:
    - ok: bool
    - response_time_ms
    - last_successful_check
    - nodes_checked
    """
    if USE_MOCK_HEALTH:
        return MOCK_RIS_STATUS

    return await ris.health_check()


@router.get(
    "/perfmon",
    summary="PerfMon health",
    response_description="Health status for PerfMon connectivity.",
)
async def perfmon_health(
    perfmon: PerfMonService = Depends(get_perfmon_service),
) -> Dict[str, Any]:
    """
    Detailed health information about PerfMon connectivity, such as:
    - ok: bool
    - response_time_ms
    - counters_sampled
    - last_successful_check
    """
    if USE_MOCK_HEALTH:
        return MOCK_PERFMON_STATUS

    return await perfmon.health_check()