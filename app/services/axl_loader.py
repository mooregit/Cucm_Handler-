"""
AXL loader utilities.

Responsibility:
- Build and cache a Zeep Client for Cisco CUCM AXL (real mode).
- Or provide a MockAXLClient in mock mode.
- Load connection settings from environment variables.
- Provide a single entrypoint `get_axl_client()` for higher-level
  services (AXLClient / routers).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Optional, Any, Dict

import requests
from zeep import Client, Settings
from zeep.transports import Transport

# Real AXLClient wrapper
from app.axl.axl_client import AXLClient


# ---------------------------------------------------------------------------
# Toggle: mock vs real AXL
# ---------------------------------------------------------------------------

USE_MOCK_AXL = os.getenv("USE_MOCK_AXL", "true").strip().lower() == "true"


# ---------------------------------------------------------------------------
# Dataclass for connection settings
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AXLConnectionParams:
    """
    All parameters required to construct a Zeep AXL client.

    Environment variable defaults:

    - CUCM_AXL_HOST           : e.g. "cucm-pub.lab.local"
    - CUCM_AXL_PORT           : default "8443"
    - CUCM_AXL_USERNAME       : AXL application user
    - CUCM_AXL_PASSWORD       : AXL application user password
    - CUCM_AXL_VERSION        : e.g. "12.5", "14.0"
    - CUCM_AXL_WSDL_PATH      : e.g. "wsdl/AXLAPI.wsdl"
    - CUCM_AXL_VERIFY_SSL     : "true" / "false" (default true)
    - CUCM_AXL_TIMEOUT        : request timeout in seconds (default 30)
    """

    host: str
    username: str
    password: str
    version: str = "14.0"
    port: int = 8443
    wsdl_path: str = "wsdl/AXLAPI.wsdl"
    verify_ssl: bool = True
    timeout: int = 30

    @property
    def service_location(self) -> str:
        return f"https://{self.host}:{self.port}/axl/"

    @property
    def resolved_wsdl(self) -> str:
        if self.wsdl_path.lower().startswith(("http://", "https://")):
            return self.wsdl_path
        return str(Path(self.wsdl_path).resolve())


# ---------------------------------------------------------------------------
# Environment loading helpers
# ---------------------------------------------------------------------------

def _str_to_bool(value: Optional[str], default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def load_params_from_env() -> AXLConnectionParams:
    """
    Load AXL connection parameters from environment variables.

    Raises RuntimeError if required vars are missing (only in real mode).
    """
    host = os.getenv("CUCM_AXL_HOST")
    username = os.getenv("CUCM_AXL_USERNAME")
    password = os.getenv("CUCM_AXL_PASSWORD")

    missing = [
        name
        for name, value in [
            ("CUCM_AXL_HOST", host),
            ("CUCM_AXL_USERNAME", username),
            ("CUCM_AXL_PASSWORD", password),
        ]
        if not value
    ]

    if missing:
        # In mock mode, we don't need real values – just return dummy params.
        if USE_MOCK_AXL:
            return AXLConnectionParams(
                host="mock-cucm",
                username="mock",
                password="mock",
                version=os.getenv("CUCM_AXL_VERSION", "14.0"),
                port=int(os.getenv("CUCM_AXL_PORT", "8443")),
                wsdl_path=os.getenv("CUCM_AXL_WSDL_PATH", "wsdl/AXLAPI.wsdl"),
                verify_ssl=_str_to_bool(os.getenv("CUCM_AXL_VERIFY_SSL"), True),
                timeout=int(os.getenv("CUCM_AXL_TIMEOUT", "30")),
            )
        # Real mode: fail fast so misconfig is obvious
        raise RuntimeError(
            f"Missing required CUCM AXL environment variables: {', '.join(missing)}"
        )

    port = int(os.getenv("CUCM_AXL_PORT", "8443"))
    version = os.getenv("CUCM_AXL_VERSION", "14.0")
    wsdl_path = os.getenv("CUCM_AXL_WSDL_PATH", "wsdl/AXLAPI.wsdl")
    verify_ssl = _str_to_bool(os.getenv("CUCM_AXL_VERIFY_SSL"), True)
    timeout = int(os.getenv("CUCM_AXL_TIMEOUT", "30"))

    return AXLConnectionParams(
        host=host,
        username=username,
        password=password,
        version=version,
        port=port,
        wsdl_path=wsdl_path,
        verify_ssl=verify_ssl,
        timeout=timeout,
    )


# ---------------------------------------------------------------------------
# Real Zeep client factory (cached)
# ---------------------------------------------------------------------------

@lru_cache(maxsize=8)
def _build_zeep_client_cached(params: AXLConnectionParams) -> Client:
    session = requests.Session()
    session.verify = params.verify_ssl
    session.auth = (params.username, params.password)

    transport = Transport(
        session=session,
        timeout=params.timeout,
    )

    settings = Settings(
        strict=False,
        xml_huge_tree=True,
    )

    client = Client(
        wsdl=params.resolved_wsdl,
        transport=transport,
        settings=settings,
    )

    # Ensure endpoint points at our CUCM host, not the WSDL default
    if client.wsdl.services:
        for service in client.wsdl.services.values():
            for port in service.ports.values():
                port.binding_options["address"] = params.service_location

    return client


# ---------------------------------------------------------------------------
# Mock AXL client (for frontend/dev without CUCM)
# ---------------------------------------------------------------------------

class MockAXLClient:
    """
    Minimal stand-in for AXLClient used when USE_MOCK_AXL=true.

    It only implements the bits the raw AXL router typically uses.
    You can extend with more fake data as you build your frontend.
    """

    # ---- Introspection used by /axl/operations ----

    def list_operations(self) -> list[str]:
        return [
            "getUser",
            "listUser",
            "getPhone",
            "listPhone",
            "executeSQLQuery",
        ]

    def get_operation_signature(self, name: str) -> str:
        return f"mock {name}(...)"

    def call(self, operation: str, **params: Any) -> Dict[str, Any]:
        # Generic mock response
        return {
            "operation": operation,
            "params": params,
            "mock": True,
        }

    # ---- Selected operations used by higher-level helpers (optional) ----

    def getUser(self, userid: str) -> Dict[str, Any]:
        return {
            "user": {
                "userid": userid,
                "firstName": "Mock",
                "lastName": "User",
                "telephoneNumber": "1000",
                "mailid": f"{userid}@example.com",
            },
            "mock": True,
        }

    def listUser(self, **kwargs: Any) -> Dict[str, Any]:
        return {
            "return": {
                "user": [
                    {
                        "userid": "userA",
                        "firstName": "User",
                        "lastName": "A",
                        "telephoneNumber": "1001",
                        "mailid": "userA@example.com",
                    },
                    {
                        "userid": "userB",
                        "firstName": "User",
                        "lastName": "B",
                        "telephoneNumber": "1002",
                        "mailid": "userB@example.com",
                    },
                ]
            },
            "mock": True,
        }

    def listPhone(self, **kwargs: Any) -> Dict[str, Any]:
        return {
            "return": {
                "phone": [
                    {
                        "name": "SEP001122334455",
                        "description": "Mock Phone A",
                        "product": "Cisco 8841",
                        "model": "Cisco 8841",
                        "devicePoolName": "DP-HQ",
                        "locationName": "HQ",
                    },
                    {
                        "name": "CSFMOCK1",
                        "description": "Mock Jabber",
                        "product": "Cisco Unified Client Services Framework",
                        "model": "CSF",
                        "devicePoolName": "DP-REMOTE",
                        "locationName": "Remote",
                    },
                ]
            },
            "mock": True,
        }

    def executeSQLQuery(self, sql: str) -> Dict[str, Any]:
        # Return deterministic fake counts for any COUNT(*) query
        return {
            "return": {
                "row": [
                    {"cnt": 42},
                ]
            },
            "mock": True,
        }

    def executeSQLUpdate(self, sql: str) -> Dict[str, Any]:
        return {
            "rowsAffected": 0,
            "mock": True,
        }


# ---------------------------------------------------------------------------
# Public API: return initialized client (real or mock)
# ---------------------------------------------------------------------------

def get_axl_client(
    params: Optional[AXLConnectionParams] = None,
) -> Any:
    """
    FastAPI dependency target.

    - In mock mode (USE_MOCK_AXL=true, default): returns MockAXLClient and
      does NOT require any CUCM_* env vars.
    - In real mode: builds a Zeep Client and wraps it in AXLClient.
    """
    if USE_MOCK_AXL:
        return MockAXLClient()

    if params is None:
        params = load_params_from_env()

    zeep_client = _build_zeep_client_cached(params)
    return AXLClient(zeep_client)
