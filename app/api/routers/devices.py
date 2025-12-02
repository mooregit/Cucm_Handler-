from typing import Any, Dict, List, Optional
import os

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.services.axl_service import AXLService, get_axl_service
from app.services.ris_service import RISService, get_ris_service
from app.dependencies.cucm_context import CucmContext, get_cucm_context

router = APIRouter(
    prefix="/devices",
    tags=["Devices"],
)

# -------------------------------------------------------------------
# Mock mode toggle
# -------------------------------------------------------------------
# Set USE_MOCK_DEVICES=false in the environment to use real CUCM services.
USE_MOCK_DEVICES = os.getenv("USE_MOCK_DEVICES", "true").lower() == "true"

# -------------------------------------------------------------------
# Mock test data
# -------------------------------------------------------------------

MOCK_DEVICES: List[Dict[str, Any]] = [
    {
        "name": "SEP001122334455",
        "description": "Test Phone – User A",
        "device_pool": "DP-HQ",
        "device_class": "Phone",
        "product": "Cisco 8841",
        "protocol": "SIP",
        "status": "Registered",
        "ip_address": "10.10.20.15",
        "cucm_node": "CUCM-PUB",
        "owner_user": "userA",
        "lines": [
            {
                "directory_number": "1001",
                "partition": "PT-HQ",
                "description": "User A main line",
            }
        ],
    },
    {
        "name": "SEP667788990000",
        "description": "Test Phone – User B",
        "device_pool": "DP-BR1",
        "device_class": "Phone",
        "product": "Cisco 8861",
        "protocol": "SIP",
        "status": "Unregistered",
        "ip_address": None,
        "cucm_node": "CUCM-SUB1",
        "owner_user": "userB",
        "lines": [
            {
                "directory_number": "2001",
                "partition": "PT-BR1",
                "description": "User B main line",
            }
        ],
    },
    {
        "name": "CSFTEST01",
        "description": "Jabber Client – User C",
        "device_pool": "DP-REMOTE",
        "device_class": "Phone",
        "product": "Cisco Unified Client Services Framework",
        "protocol": "SIP",
        "status": "Registered",
        "ip_address": "10.10.30.50",
        "cucm_node": "CUCM-PUB",
        "owner_user": "userC",
        "lines": [
            {
                "directory_number": "3001",
                "partition": "PT-REMOTE",
                "description": "User C softphone",
            }
        ],
    },
]


def _filter_mock_devices(
    name: Optional[str],
    device_pool: Optional[str],
) -> List[Dict[str, Any]]:
    devices = MOCK_DEVICES
    if name:
        n = name.lower()
        devices = [d for d in devices if n in d["name"].lower()]
    if device_pool:
        dp = device_pool.lower()
        devices = [d for d in devices if d.get("device_pool", "").lower() == dp]
    return devices


# -------------------------------------------------------------------
# Endpoints
# -------------------------------------------------------------------


@router.get(
    "",
    summary="List CUCM devices",
    response_description="List of CUCM devices (thin representation from AXL or mock data).",
)
async def list_devices(
    name: Optional[str] = Query(
        default=None,
        description="Optional device name (exact or pattern depending on service implementation).",
    ),
    device_pool: Optional[str] = Query(
        default=None,
        description="Optional device pool filter.",
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=500,
        description="Maximum number of devices to return.",
    ),
    offset: int = Query(
        default=0,
        ge=0,
        description="Offset for pagination.",
    ),
    axl: AXLService = Depends(get_axl_service),
) -> List[Dict[str, Any]]:
    """
    High-level device listing endpoint.

    In mock mode, returns static test data with simple filtering and pagination.
    Otherwise, delegates to AXLService.
    """
    if USE_MOCK_DEVICES:
        devices = _filter_mock_devices(name=name, device_pool=device_pool)
        return devices[offset : offset + limit]

    devices = await axl.list_devices(
        name=name,
        device_pool=device_pool,
        limit=limit,
        offset=offset,
    )
    return devices


@router.get(
    "/count",
    summary="Get total number of CUCM devices",
    response_description="Count of devices matching optional filters.",
)
async def count_devices(
    device_pool: Optional[str] = Query(
        default=None,
        description="Optional device pool filter.",
    ),
    axl: AXLService = Depends(get_axl_service),
) -> Dict[str, int]:
    """
    Return the count of devices matching the given filters.

    Uses mock data in mock mode, otherwise AXLService.
    """
    if USE_MOCK_DEVICES:
        devices = _filter_mock_devices(name=None, device_pool=device_pool)
        return {"count": len(devices)}

    count = await axl.count_devices(device_pool=device_pool)
    return {"count": count}


@router.get(
    "/{device_name}",
    summary="Get device details",
    response_description="Full device details from AXL or mock data.",
)
async def get_device(
    device_name: str,
    axl: AXLService = Depends(get_axl_service),
) -> Dict[str, Any]:
    """
    Get detailed information about a single device (phone, gateway, etc.)
    by its CUCM device name.
    """
    if USE_MOCK_DEVICES:
        device = next((d for d in MOCK_DEVICES if d["name"] == device_name), None)
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Device '{device_name}' not found",
            )
        return device

    device = await axl.get_device(device_name=device_name)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device '{device_name}' not found",
        )
    return device


@router.get(
    "/{device_name}/lines",
    summary="Get lines configured on a device",
    response_description="List of lines (DNs) configured on a device.",
)
async def get_device_lines(
    device_name: str,
    axl: AXLService = Depends(get_axl_service),
) -> List[Dict[str, Any]]:
    """
    Return the lines/DNs configured on the given device.
    """
    if USE_MOCK_DEVICES:
        device = next((d for d in MOCK_DEVICES if d["name"] == device_name), None)
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Device '{device_name}' not found",
            )
        return device.get("lines", [])

    lines = await axl.get_device_lines(device_name=device_name)
    return lines


@router.get(
    "/{device_name}/status",
    summary="Get device registration/status",
    response_description="Registration and status details for a device from RIS or mock data.",
)
async def get_device_status(
    device_name: str,
    ris: RISService = Depends(get_ris_service),
) -> Dict[str, Any]:
    """
    Get registration/status information for a specific device from RIS.

    Typical fields include:
    - registration_status
    - ip_address
    - cucm_node
    - protocol
    - last_update
    """
    if USE_MOCK_DEVICES:
        device = next((d for d in MOCK_DEVICES if d["name"] == device_name), None)
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Status for device '{device_name}' not found",
            )
        return {
            "device_name": device["name"],
            "registration_status": device.get("status", "Unknown"),
            "ip_address": device.get("ip_address"),
            "cucm_node": device.get("cucm_node"),
            "protocol": device.get("protocol"),
            "last_update": "2025-01-01T12:00:00Z",
        }

    status_info = await ris.get_device_status(device_name=device_name)
    if not status_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Status for device '{device_name}' not found",
        )
    return status_info


@router.get(
    "/registered",
    summary="List currently registered devices (RIS)",
    response_description="List of devices currently registered in the cluster.",
)
async def list_registered_devices(
    cucm_node: Optional[str] = Query(
        default=None,
        description="Optional filter for a specific CUCM node/CMG.",
    ),
    device_class: Optional[str] = Query(
        default=None,
        description="Optional device class filter (Phone, Gateway, etc.).",
    ),
    limit: int = Query(
        default=200,
        ge=1,
        le=1000,
        description="Maximum number of devices to return.",
    ),
    ris: RISService = Depends(get_ris_service),
) -> List[Dict[str, Any]]:
    """
    List currently registered devices using the RISPort API.

    In mock mode, returns a subset of MOCK_DEVICES with status 'Registered'.
    """
    if USE_MOCK_DEVICES:
        devices = [d for d in MOCK_DEVICES if d.get("status") == "Registered"]
        if cucm_node:
            cn = cucm_node.lower()
            devices = [d for d in devices if d.get("cucm_node", "").lower() == cn]
        if device_class:
            dc = device_class.lower()
            devices = [d for d in devices if d.get("device_class", "").lower() == dc]

        # Map to a RIS-like shape
        ris_devices = [
            {
                "device_name": d["name"],
                "ip_address": d.get("ip_address"),
                "cucm_node": d.get("cucm_node"),
                "protocol": d.get("protocol"),
                "registration_status": d.get("status"),
            }
            for d in devices
        ]
        return ris_devices[:limit]

    devices = await ris.list_registered_devices(
        cucm_node=cucm_node,
        device_class=device_class,
        limit=limit,
    )
    return devices


@router.get(
    "/summary",
    summary="Get device summary metrics",
    response_description="High-level metrics about devices in the cluster.",
)
async def get_device_summary(
    axl: AXLService = Depends(get_axl_service),
    ris: RISService = Depends(get_ris_service),
) -> Dict[str, Any]:
    """
    Aggregate view of device-related metrics, combining AXL and RIS.

    In mock mode, computes summary statistics from MOCK_DEVICES.
    """
    if USE_MOCK_DEVICES:
        total_devices = len(MOCK_DEVICES)
        total_registered = sum(1 for d in MOCK_DEVICES if d.get("status") == "Registered")
        total_unregistered = sum(1 for d in MOCK_DEVICES if d.get("status") == "Unregistered")

        by_device_pool: Dict[str, Dict[str, int]] = {}
        for d in MOCK_DEVICES:
            pool = d.get("device_pool", "UNKNOWN")
            status = d.get("status")
            bucket = by_device_pool.setdefault(
                pool, {"total": 0, "registered": 0, "unregistered": 0}
            )
            bucket["total"] += 1
            if status == "Registered":
                bucket["registered"] += 1
            elif status == "Unregistered":
                bucket["unregistered"] += 1

        by_type: Dict[str, Dict[str, int]] = {}
        for d in MOCK_DEVICES:
            t = d.get("device_class", "Unknown")
            status = d.get("status")
            bucket = by_type.setdefault(
                t, {"total": 0, "registered": 0, "unregistered": 0}
            )
            bucket["total"] += 1
            if status == "Registered":
                bucket["registered"] += 1
            elif status == "Unregistered":
                bucket["unregistered"] += 1

        return {
            "axl": {
                "total_devices": total_devices,
                "by_device_pool": by_device_pool,
                "by_type": by_type,
            },
            "ris": {
                "total_registered": total_registered,
                "total_unregistered": total_unregistered,
            },
        }

    axl_stats = await axl.get_device_statistics()
    ris_stats = await ris.get_registered_statistics()

    return {
        "axl": axl_stats,
        "ris": ris_stats,
    }
