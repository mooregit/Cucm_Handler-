from __future__ import annotations

import warnings
from typing import Any, Callable, List

from requests import Session
from requests.auth import HTTPBasicAuth
from zeep import Client, Settings
from zeep.exceptions import Fault
from zeep.transports import Transport


class RISClient:
    """
    Thin wrapper around Cisco RISPort SOAP (Real-Time Information Service).

    - Loads RISService70.wsdl
    - Creates a binding for RISService70
    - Exposes generic .call(operation, **params)
    - Optionally autogenerates methods per operation
    """

    def __init__(
        self,
        wsdl_path: str,
        host: str,
        username: str,
        password: str,
        verify_ssl: bool = False,
        timeout: int = 20,
    ) -> None:
        """
        :param wsdl_path: Path to RISService70.wsdl
        :param host: CUCM Publisher hostname or IP
        :param username: App user with RIS permissions
        :param password: password
        :param verify_ssl: Verify HTTPS certificate
        :param timeout: HTTP timeout (seconds)
        """

        warnings.filterwarnings("ignore", category=UserWarning)

        self.wsdl_path = wsdl_path
        self.host = host

        session = Session()
        session.auth = HTTPBasicAuth(username, password)
        session.verify = verify_ssl

        transport = Transport(session=session, timeout=timeout)
        settings = Settings(strict=False, xml_huge_tree=True)

        self.client = Client(wsdl=wsdl_path, transport=transport, settings=settings)

        # RISPort endpoint is typically /realtimeservice/services/RISService70
        self._service = self.client.create_service(
            "{http://schemas.cisco.com/ast/soap}RisBinding",
            f"https://{host}:8443/realtimeservice/services/RISService70",
        )

        self._attach_operations()

    # ------------------------------------------------------------------ #
    # Core generic call
    # ------------------------------------------------------------------ #

    def call(self, operation: str, **params: Any) -> Any:
        try:
            op = getattr(self._service, operation)
        except AttributeError as exc:
            raise ValueError(f"Unknown RIS operation: {operation}") from exc

        try:
            return op(**params)
        except Fault as fault:
            raise RuntimeError(f"RIS SOAP Fault in '{operation}': {fault}") from fault

    # ------------------------------------------------------------------ #
    # Introspection
    # ------------------------------------------------------------------ #

    def _get_port(self):
        service = self.client.wsdl.services["RisService"]
        return service.ports["RisBinding"]

    def list_operations(self) -> List[str]:
        return sorted(self._get_port().operations.keys())

    def get_operation_signature(self, operation: str) -> str:
        port = self._get_port()
        try:
            return port.operations[operation].signature()
        except KeyError:
            raise ValueError(f"Unknown RIS operation: {operation}")

    # ------------------------------------------------------------------ #
    # Dynamic method generation
    # ------------------------------------------------------------------ #

    def _attach_operations(self) -> None:
        port = self._get_port()

        for op_name, op in port.operations.items():
            if hasattr(self, op_name):
                continue

            def _make_method(name: str) -> Callable[..., Any]:
                def _method(self, **params: Any) -> Any:
                    return self.call(name, **params)

                _method.__name__ = name
                try:
                    _method.__doc__ = f"RIS operation: {name}\n\n{op.signature()}"
                except Exception:
                    _method.__doc__ = f"RIS operation: {name}"
                return _method

            method = _make_method(op_name)
            setattr(self.__class__, op_name, method)