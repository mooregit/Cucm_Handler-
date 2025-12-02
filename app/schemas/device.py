from typing import Optional, List

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Line schemas
# ---------------------------------------------------------------------------

class LineBase(BaseModel):
    """
    Basic representation of a line/DN associated with a device.
    """
    directory_number: str = Field(..., min_length=1, max_length=32)
    partition: Optional[str] = Field(default=None, max_length=64)
    description: Optional[str] = Field(default=None, max_length=128)

    class Config:
        orm_mode = True


class LineCreate(LineBase):
    """
    Schema for creating a new line/DN.
    """
    pass


class LineUpdate(BaseModel):
    """
    Schema for updating an existing line/DN (partial).
    """
    directory_number: Optional[str] = Field(default=None, min_length=1, max_length=32)
    partition: Optional[str] = Field(default=None, max_length=64)
    description: Optional[str] = Field(default=None, max_length=128)

    class Config:
        orm_mode = True


class LineRead(LineBase):
    """
    Schema for reading/returning a line/DN.
    """
    id: int

    class Config:
        orm_mode = True


# ---------------------------------------------------------------------------
# Phone/device schemas
# ---------------------------------------------------------------------------

class PhoneBase(BaseModel):
    """
    Shared properties for phone/device objects stored in the local DB.
    This is independent of raw CUCM AXL responses, but should roughly
    match what you care about in the UI.
    """

    name: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="CUCM device name (e.g., SEP001122334455, CSFUSER1).",
    )
    description: Optional[str] = Field(
        default=None,
        max_length=128,
        description="Friendly description for the device.",
    )
    device_pool: Optional[str] = Field(
        default=None,
        max_length=64,
        description="Logical device pool in CUCM.",
    )
    device_class: Optional[str] = Field(
        default="Phone",
        max_length=32,
        description="Device class (Phone, Gateway, etc.).",
    )
    product: Optional[str] = Field(
        default=None,
        max_length=128,
        description="Product type (e.g., Cisco 8841, Cisco 8861).",
    )
    protocol: Optional[str] = Field(
        default=None,
        max_length=32,
        description="Signaling protocol (e.g., SIP, SCCP).",
    )
    location: Optional[str] = Field(
        default=None,
        max_length=64,
        description="CUCM location for CAC.",
    )
    owner_user: Optional[str] = Field(
        default=None,
        max_length=64,
        description="Associated end user ID in CUCM.",
    )
    mac_address: Optional[str] = Field(
        default=None,
        max_length=17,
        description="Optional MAC address (for physical phones).",
    )
    tenant_id: Optional[int] = Field(
        default=None,
        description="Optional tenant association for multi-tenant deployments.",
    )

    class Config:
        orm_mode = True


class PhoneCreate(PhoneBase):
    """
    Schema for creating a phone/device record in the local DB.
    Lines can optionally be supplied at create time.
    """

    lines: Optional[List[LineCreate]] = Field(
        default=None,
        description="Optional list of lines (DNs) to associate with the phone.",
    )


class PhoneUpdate(BaseModel):
    """
    Schema for updating an existing phone/device.
    All fields are optional for partial updates.
    """

    name: Optional[str] = Field(default=None, min_length=1, max_length=64)
    description: Optional[str] = Field(default=None, max_length=128)
    device_pool: Optional[str] = Field(default=None, max_length=64)
    device_class: Optional[str] = Field(default=None, max_length=32)
    product: Optional[str] = Field(default=None, max_length=128)
    protocol: Optional[str] = Field(default=None, max_length=32)
    location: Optional[str] = Field(default=None, max_length=64)
    owner_user: Optional[str] = Field(default=None, max_length=64)
    mac_address: Optional[str] = Field(default=None, max_length=17)
    tenant_id: Optional[int] = None

    class Config:
        orm_mode = True


class PhoneRead(PhoneBase):
    """
    Schema for reading a phone/device from the API.
    """

    id: int = Field(..., description="Primary key of the phone record.")
    lines: Optional[List[LineRead]] = None

    class Config:
        orm_mode = True
