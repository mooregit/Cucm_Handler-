# app/axl/axl_client.py

from __future__ import annotations

import warnings
from typing import Any, Callable, List

from requests import Session
from requests.auth import HTTPBasicAuth
from zeep import Client, Settings
from zeep.exceptions import Fault
from zeep.transports import Transport


class AXLClient:
    """
    A dynamic AXL SOAP client that:

    - Loads the CUCM AXL WSDL
    - Creates all SOAP methods automatically as Python methods
    - Exposes generic .call(name, **params)
    - Provides introspection helpers
    """

    def __init__(
        self,
        wsdl_path: str,
        host: str,
        username: str,
        password: str,
        axl_version: str = "14.0",
        verify_ssl: bool = False,
        timeout: int = 20,
    ) -> None:
        """
        :param wsdl_path: Local AXLAPI.wsdl path
        :param host: CUCM Publisher FQDN or IP
        :param username: AXL user
        :param password: AXL password
        :param axl_version: Must match the WSDL version (10.5, 11.0, 12.5, 14.0, etc.)
        :param verify_ssl: Verify TLS cert. False is common in labs.
        :param timeout: HTTP timeout
        """

        # Silence "No schema" warnings that Cisco's WSDL triggers
        warnings.filterwarnings("ignore", category=UserWarning)

        self.wsdl_path = wsdl_path
        self.host = host
        self.axl_version = axl_version

        # HTTP auth + transport for Zeep
        session = Session()
        session.auth = HTTPBasicAuth(username, password)
        session.verify = verify_ssl

        transport = Transport(session=session, timeout=timeout)
        settings = Settings(strict=False, xml_huge_tree=True)

        # Load WSDL
        self.client = Client(wsdl=wsdl_path, transport=transport, settings=settings)

        # Create binding endpoint
        self._service = self.client.create_service(
            f"{{http://www.cisco.com/AXL/API/{axl_version}}}AXLAPIBinding",
            f"https://{host}:8443/axl/",
        )

        # Auto-build: getUser(), addUser(), getPhone(), etc.
        self._attach_operations()

    # ============================================================================
    # Core generic call
    # ============================================================================

    def call(self, operation: str, **params: Any) -> Any:
        """
        Calls any AXL SOAP operation by name.

        Example:
            axl.call("getUser", userid="jdoe")
        """
        try:
            soap_op = getattr(self._service, operation)
        except AttributeError as exc:
            raise ValueError(f"Unknown AXL operation: {operation}") from exc

        try:
            return soap_op(**params)
        except Fault as fault:
            raise RuntimeError(f"AXL SOAP Fault in '{operation}': {fault}") from fault

    # ============================================================================
    # WSDL introspection
    # ============================================================================

    def _get_port(self):
        service = self.client.wsdl.services["AXLAPIService"]
        return service.ports["AXLAPIBinding"]

    def list_operations(self) -> List[str]:
        """Return list of all WSDL-defined AXL operations."""
        return sorted(self._get_port().operations.keys())

    def get_operation_signature(self, operation: str) -> str:
        """Return human-readable SOAP signature for an operation."""
        port = self._get_port()
        try:
            return port.operations[operation].signature()
        except KeyError:
            raise ValueError(f"Unknown AXL operation: {operation}")

    # ============================================================================
    # Dynamic method generation
    # ============================================================================

    def _attach_operations(self) -> None:
        """
        Creates a Python function for every AXL SOAP operation.

        Example:

            def getUser(self, **params):
                return self.call("getUser", **params)
        """
        port = self._get_port()

        for op_name, op in port.operations.items():
            # Skip if method already defined
            if hasattr(self, op_name):
                continue

            # Build a closure binding op_name
            def _make_method(name: str) -> Callable[..., Any]:
                def _method(self, **params: Any) -> Any:
                    return self.call(name, **params)

                _method.__name__ = name

                try:
                    _method.__doc__ = f"AXL operation: {name}\n\n{op.signature()}"
                except Exception:
                    _method.__doc__ = f"AXL operation: {name}"

                return _method

            method = _make_method(op_name)

            # Attach method to the class so all instances share it
            setattr(self.__class__, op_name, method)