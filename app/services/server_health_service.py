# app/services/server_health_service.py

from __future__ import annotations

from typing import Any, Dict, List, Optional

import asyncio
from datetime import datetime, timezone

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Adjust these imports to match your actual project layout/models.
from app.db.session import get_db
from app.services.axl_service import AXLService, get_axl_service
from app.services.ris_service import RISService, get_ris_service
from app.services.perfmon_service import (
    PerfMonService,
    get_perfmon_service,
)

# Example model import; update to match your real model/module name.
# Assumed fields:
#   id: int
#   name: str
#   fqdn: str
#   server_type: str  ("cucm", "unity", "expressway", "uccx", "imp", "cube", "cer", "cms", ...)
#   cluster_name: Optional[str]
#   is_enabled: bool
#   mgmt_address: Optional[str] (fallback if fqdn not set)
#   ports: Optional[list[int]] or JSON-encoded list
from app.models.uc_server import UcServer  # type: ignore


class ServerHealthService:
    """
    Aggregates health information for UC servers (CUCM, Unity, Expressway, etc.).

    This service is intentionally generic; it:
      - Reads servers from the DB (UcServer table).
      - Performs cheap generic checks (TCP port checks).
      - Delegates CUCM-specific checks to AXL/RIS/PerfMon services.
    """

    def __init__(
        self,
        db: AsyncSession,
        axl: AXLService,
        ris: RISService,
        perfmon: PerfMonService,
    ) -> None:
        self.db = db
        self.axl = axl
        self.ris = ris
        self.perfmon = perfmon

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    async def get_all_servers_health(self) -> List[Dict[str, Any]]:
        """
        Return health info for all enabled servers.
        """
        stmt = select(UcServer).where(UcServer.is_enabled == True)  # type: ignore[comparison-overlap]
        result = await self.db.execute(stmt)
        servers: List[UcServer] = list(result.scalars().all())

        data: List[Dict[str, Any]] = []
        for server in servers:
            data.append(await self._build_server_health(server))
        return data

    async def get_server_health(self, server_id: int) -> Optional[Dict[str, Any]]:
        """
        Return health info for a single server by ID, or None if not found.
        """
        stmt = select(UcServer).where(UcServer.id == server_id)
        result = await self.db.execute(stmt)
        server: Optional[UcServer] = result.scalars().first()

        if server is None:
            return None

        return await self._build_server_health(server)

    # -------------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------------

    async def _build_server_health(self, server: UcServer) -> Dict[str, Any]:
        """
        Build a consolidated health object for a single server.
        """
        target_host = getattr(server, "mgmt_address", None) or getattr(server, "fqdn", None)
        ports = self._get_ports_for_server(server)

        # Run checks concurrently where possible
        checks = []

        # Generic TCP checks
        tcp_tasks = [
            self._check_tcp_port(target_host, port) for port in ports if target_host
        ]
        checks.extend(tcp_tasks)

        # CUCM-specific checks
        axl_task = None
        ris_task = None
        perfmon_task = None

        if server.server_type == "cucm":
            axl_task = asyncio.create_task(self._check_axl_for_server(server))
            ris_task = asyncio.create_task(self._check_ris_for_server(server))
            perfmon_task = asyncio.create_task(self._check_perfmon_for_server(server))

        results = await asyncio.gather(*checks, return_exceptions=True)

        ports_status: Dict[str, Any] = {}
        for idx, port in enumerate(ports):
            if idx >= len(results):
                break
            result = results[idx]
            if isinstance(result, Exception):
                ports_status[str(port)] = {"ok": False, "error": repr(result)}
            else:
                ports_status[str(port)] = result

        # Collect AXL/RIS/PerfMon results if applicable
        axl_status: Optional[Dict[str, Any]] = None
        ris_status: Optional[Dict[str, Any]] = None
        perfmon_status: Optional[Dict[str, Any]] = None

        if axl_task:
            axl_status = await axl_task
        if ris_task:
            ris_status = await ris_task
        if perfmon_task:
            perfmon_status = await perfmon_task

        # Compute overall_ok based on available checks
        ok_components = [
            v
            for v in [
                axl_status,
                ris_status,
                perfmon_status,
            ]
            if v is not None
        ]
        # If no protocol-specific checks exist, fall back to ports.
        if not ok_components:
            ok_components = list(ports_status.values())

        overall_ok = all(c.get("ok", False) for c in ok_components) if ok_components else False

        return {
            "id": server.id,
            "name": server.name,
            "fqdn": getattr(server, "fqdn", None),
            "server_type": server.server_type,
            "cluster_name": getattr(server, "cluster_name", None),
            "enabled": server.is_enabled,
            "target_host": target_host,
            "ok": overall_ok,
            "status": {
                "ports": ports_status,
                "axl": axl_status,
                "ris": ris_status,
                "perfmon": perfmon_status,
            },
            "last_checked": datetime.now(timezone.utc).isoformat(),
        }

    def _get_ports_for_server(self, server: UcServer) -> List[int]:
        """
        Determine which ports to check for a given server.

        You can customize this to derive ports from:
          - server.ports (JSON/list field)
          - server.server_type (defaults per type)
        """
        # If the model has an explicit ports field (list[int] or JSON), prefer it.
        ports = getattr(server, "ports", None)
        if isinstance(ports, list) and all(isinstance(p, int) for p in ports):
            return ports

        # Fallback defaults by type
        defaults_by_type = {
            "cucm": [8443, 443],
            "unity": [7071, 443],
            "expressway": [8443, 443],
            "uccx": [8443, 443],
            "imp": [8443, 443],
            "cube": [5060, 5061],
            "cer": [8443, 443],
            "cms": [443],
        }

        return defaults_by_type.get(getattr(server, "server_type", "").lower(), [443])

    # -------------------------------------------------------------------------
    # Low-level check primitives
    # -------------------------------------------------------------------------

    async def _check_tcp_port(self, host: str, port: int, timeout: float = 2.0) -> Dict[str, Any]:
        """
        Simple TCP connect check to verify that a port is reachable.
        """
        result: Dict[str, Any] = {"ok": False, "port": port}
        if not host:
            result["error"] = "no_host"
            return result

        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=timeout,
            )
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass
            result["ok"] = True
            return result
        except asyncio.TimeoutError:
            result["error"] = "timeout"
        except OSError as exc:
            result["error"] = f"os_error: {exc}"
        except Exception as exc:  # noqa: BLE001
            result["error"] = f"unknown_error: {exc}"

        return result

    # -------------------------------------------------------------------------
    # CUCM-specific wrappers
    # -------------------------------------------------------------------------

    async def _check_axl_for_server(self, server: UcServer) -> Dict[str, Any]:
        """
        Delegate AXL check to AXLService.

        Extend AXLService with a server-scoped method if you need per-node checks.
        For now this calls the cluster-level `health_check()` as a placeholder.
        """
        try:
            status = await self.axl.health_check()
            # Optionally annotate which server we intended
            status.setdefault("target_server_id", server.id)
            return status
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": f"axl_error: {exc}", "target_server_id": server.id}

    async def _check_ris_for_server(self, server: UcServer) -> Dict[str, Any]:
        """
        Delegate RIS check to RISService.
        """
        try:
            status = await self.ris.health_check()
            status.setdefault("target_server_id", server.id)
            return status
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": f"ris_error: {exc}", "target_server_id": server.id}

    async def _check_perfmon_for_server(self, server: UcServer) -> Dict[str, Any]:
        """
        Delegate PerfMon check to PerfMonService.
        """
        try:
            status = await self.perfmon.health_check()
            status.setdefault("target_server_id", server.id)
            return status
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": f"perfmon_error: {exc}", "target_server_id": server.id}


# -------------------------------------------------------------------------
# FastAPI dependency
# -------------------------------------------------------------------------


def get_server_health_service(
    db: AsyncSession = Depends(get_db),
    axl: AXLService = Depends(get_axl_service),
    ris: RISService = Depends(get_ris_service),
    perfmon: PerfMonService = Depends(get_perfmon_service),
) -> ServerHealthService:
    """
    Dependency injector for ServerHealthService.
    """
    return ServerHealthService(db=db, axl=axl, ris=ris, perfmon=perfmon)
