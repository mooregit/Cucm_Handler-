from __future__ import annotations

import os
from functools import lru_cache

from app.perfmon.perfmon_client import PerfmonClient


@lru_cache(maxsize=1)
def get_perfmon_client() -> PerfmonClient:
    wsdl_path = os.getenv("CUCM_PERFMON_WSDL", "app/perfmon/schema/PerfmonService.wsdl")
    host = os.getenv("CUCM_HOST")
    username = os.getenv("CUCM_PERFMON_USERNAME", os.getenv("CUCM_USERNAME"))
    password = os.getenv("CUCM_PERFMON_PASSWORD", os.getenv("CUCM_PASSWORD"))
    verify_ssl = os.getenv("CUCM_VERIFY_SSL", "false").lower() == "true"

    if not (host and username and password):
        raise RuntimeError("CUCM_HOST, CUCM_PERFMON_USERNAME, CUCM_PERFMON_PASSWORD must be set")

    return PerfmonClient(
        wsdl_path=wsdl_path,
        host=host,
        username=username,
        password=password,
        verify_ssl=verify_ssl,
    )