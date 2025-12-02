# app/api/router_axl_raw.py

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field

from app.axl.axl_client import AXLClient
from app.services.axl_loader import get_axl_client

router = APIRouter(tags=["AXL (raw)"])


class AxlCallRequest(BaseModel):
    """
    Generic payload wrapper for raw AXL calls.

    The `params` dict is passed directly through to the underlying
    AXL SOAP method as keyword arguments.
    """
    params: Dict[str, Any] = Field(
        default_factory=dict,
        description="Raw AXL parameters to pass as **kwargs to the SOAP operation.",
    )


@router.get(
    "/operations",
    summary="List all available AXL operations",
    description="Returns all AXL SOAP operation names discovered from the WSDL.",
)
def list_axl_operations(axl: AXLClient = Depends(get_axl_client)) -> Dict[str, Any]:
    try:
        operations = axl.list_operations()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to list AXL operations: {exc}")
    return {"operations": operations}


@router.get(
    "/operations/{name}",
    summary="Get AXL operation signature",
    description="Returns a human-readable signature for a specific AXL SOAP operation.",
)
def get_axl_operation_signature(
    name: str,
    axl: AXLClient = Depends(get_axl_client),
) -> Dict[str, str]:
    try:
        signature = axl.get_operation_signature(name)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Unknown AXL operation: {name}")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to inspect AXL operation: {exc}")

    return {"operation": name, "signature": signature}


@router.post(
    "/{operation}",
    summary="Call raw AXL operation",
    description=(
        "Proxy any AXL SOAP operation by name. "
        "Body should contain `params`, which are passed directly as keyword arguments."
    ),
)
async def axl_call(
    operation: str,
    payload: AxlCallRequest,
    axl: AXLClient = Depends(get_axl_client),
) -> Any:
    """
    Generic raw AXL proxy.

    Example:

        POST /axl/getUser
        {
          "params": {
            "userid": "jdoe"
          }
        }
    """
    try:
        result = axl.call(operation, **payload.params)
    except ValueError:
        # Unknown operation name
        raise HTTPException(status_code=404, detail=f"Unknown AXL operation: {operation}")
    except RuntimeError as exc:
        # AXL SOAP Fault or other AXL-level error
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        # Unexpected internal error
        raise HTTPException(status_code=500, detail=f"AXL call failed: {exc}")

    # Ensure zeep objects are JSON-serializable
    return jsonable_encoder(result)