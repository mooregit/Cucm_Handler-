from __future__ import annotations

import os
from functools import lru_cache

from app.ris.ris_client import RISClient


@lru_cache(maxsize=1)
def get_ris_client() -> RISClient:
    wsdl_path = os.getenv("CUCM_RIS_WSDL", "app/ris/schema/RISService70.wsdl")
    host = os.getenv("CUCM_HOST")
    username = os.getenv("CUCM_RIS_USERNAME", os.getenv("CUCM_USERNAME"))
    password = os.getenv("CUCM_RIS_PASSWORD", os.getenv("CUCM_PASSWORD"))
    verify_ssl = os.getenv("CUCM_VERIFY_SSL", "false").lower() == "true"

    if not (host and username and password):
        raise RuntimeError("CUCM_HOST, CUCM_RIS_USERNAME, CUCM_RIS_PASSWORD must be set")

    return RISClient(
        wsdl_path=wsdl_path,
        host=host,
        username=username,
        password=password,
        verify_ssl=verify_ssl,
    )