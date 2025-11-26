from pydantic import BaseModel, Field
from typing import List, Optional
from .common import CUCMBase


class RISPortBase(CUCMBase):
    node: Optional[str] = Field(None, example="cucm-pub")


class RISDeviceQueryRequest(RISPortBase):
    device_names: List[str] = Field(..., example=["SEP001122334455"])


class RISDeviceStatus(BaseModel):
    name: str
    status: str
    ip: Optional[str] = None
    device_type: Optional[str] = None
    protocol: Optional[str] = None
    time_stamp: Optional[str] = None


class RISDeviceQueryResponse(BaseModel):
    results: List[RISDeviceStatus]