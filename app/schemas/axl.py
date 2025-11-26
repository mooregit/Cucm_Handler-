from pydantic import BaseModel, Field
from typing import List, Optional
from .common import CUCMBase


# ---------- RAW AXL REQUEST ----------
class AXLRawRequest(CUCMBase):
    method: str = Field(..., example="getPhone")
    body: dict = Field(..., example={"name": "SEP1234567890AB"})


class AXLRawResponse(BaseModel):
    success: bool
    response: dict | None = None
    error: str | None = None


# ---------- DEVICE & USER MODELS ----------
class Device(BaseModel):
    name: str
    description: Optional[str] = None
    product: Optional[str] = None
    model: Optional[str] = None
    protocol: Optional[str] = None
    status: Optional[str] = None


class User(BaseModel):
    userid: str
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    telephone_number: Optional[str] = None


# ---------- HIGH-LEVEL STATUS MODELS ----------
class CUCMDeviceCountResponse(BaseModel):
    total_devices: int
    registered: int
    unregistered: int
    rejected: int
    unknown: int


class CUCMUserCountResponse(BaseModel):
    total_users: int


class CUCMDeviceListResponse(BaseModel):
    devices: List[Device]


class CUCMUserListResponse(BaseModel):
    users: List[User]


class Trunk(BaseModel):
    name: str
    device_pool: Optional[str] = None
    status: Optional[str] = None


class CUCMTrunkListResponse(BaseModel):
    trunks: List[Trunk]


class CUCMTrunkCountResponse(BaseModel):
    total_trunks: int
    active_trunks: Optional[int] = None
    inactive_trunks: Optional[int] = None


class CUCMSystemStatusResponse(BaseModel):
    cucm_version: str
    db_cluster_state: str
    nodes: List[str]
    uptime_hours: Optional[int] = None