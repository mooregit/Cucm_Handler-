# app/api/routers/ris_raw.py

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.services.ris_service import RISService, get_ris_service


router = APIRouter(
    prefix="/ris",
    tags=["RIS (raw)"],
)


@router.get(
    "/health",
    summary="RISPort health check",
    response_description="Basic health status from RISService.",
)
async def ris_health(
    ris: RISService = Depends(get_ris_service),
) -> Dict[str, Any]:
    """
    Lightweight RIS health probe – uses RISService.health_check().
    """
    try:
        return await ris.health_check()
    except RuntimeError as exc:
        # Typically indicates RISClient is not configured.
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"RIS health check failed: {exc}")


@router.get(
    "/devices/registered",
    summary="List registered devices (RIS)",
    response_description="Real-time list of registered devices from RIS.",
)
async def list_registered_devices(
    cucm_node: Optional[str] = Query(
        default=None,
        description="Optional CUCM node name filter (processnode.name).",
    ),
    device_class: Optional[str] = Query(
        default="Phone",
        description="RIS device class (Phone, Gateway, Any, etc.).",
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
    Return devices currently registered according to RISPort.

    This corresponds to SelectCmDevice under the hood.
    """
    try:
        devices = await ris.list_registered_devices(
            cucm_node=cucm_node,
            device_class=device_class,
            limit=limit,
        )
        return devices
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"RIS devices query failed: {exc}")


@router.get(
    "/devices/{device_name}/status",
    summary="Get real-time device status (RIS)",
    response_description="Registration/IP/node info for a single device.",
)
async def get_device_status(
    device_name: str,
    ris: RISService = Depends(get_ris_service),
) -> Dict[str, Any]:
    """
    Look up real-time registration/status for a specific device by name.
    """
    try:
        status_info = await ris.get_device_status(device_name=device_name)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"RIS device status failed: {exc}")

    if not status_info:
        raise HTTPException(status_code=404, detail=f"Device '{device_name}' not found in RIS")

    return status_info


@router.get(
    "/trunks",
    summary="List registered trunks (RIS)",
    response_description="Real-time list of trunks (gateway class) from RIS.",
)
async def list_registered_trunks(
    pattern: str = Query(
        default="%",
        description="Optional trunk name pattern (SQL-like wildcard).",
    ),
    limit: int = Query(
        default=200,
        ge=1,
        le=1000,
        description="Maximum number of trunks to return.",
    ),
    ris: RISService = Depends(get_ris_service),
) -> List[Dict[str, Any]]:
    """
    Return trunks (treated as Gateway class in RIS) matching the given pattern.
    """
    try:
        trunks = await ris.get_registered_trunks(pattern=pattern)
        return trunks[:limit]
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"RIS trunks query failed: {exc}")


@router.get(
    "/trunks/summary",
    summary="Trunk status summary (RIS)",
    response_description="Aggregated up/down/unknown counts for trunks.",
)
async def trunk_status_summary(
    pattern: str = Query(
        default="%",
        description="Optional trunk name pattern (SQL-like wildcard).",
    ),
    ris: RISService = Depends(get_ris_service),
) -> Dict[str, Any]:
    """
    High-level summary of trunk registration status using RIS.

    NOTE: This is registration/status only, not call-path performance.
    """
    try:
        summary = await ris.get_trunk_status_summary(pattern=pattern)
        return summary
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"RIS trunk summary failed: {exc}")
