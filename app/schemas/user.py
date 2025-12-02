from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """
    Shared properties for User objects.
    """

    username: str = Field(..., min_length=1, max_length=64)
    email: Optional[EmailStr] = Field(
        default=None,
        description="Optional email address for the user.",
    )
    full_name: Optional[str] = Field(
        default=None,
        max_length=128,
        description="Optional display name.",
    )
    is_active: bool = Field(
        default=True,
        description="Indicates if the user account is active.",
    )
    is_superuser: bool = Field(
        default=False,
        description="Indicates if the user has administrative privileges.",
    )
    tenant_id: Optional[int] = Field(
        default=None,
        description="Optional tenant association for multi-tenant environments.",
    )

    class Config:
        orm_mode = True


class UserCreate(UserBase):
    """
    Schema for creating a new user.
    """

    password: str = Field(
        ...,
        min_length=6,
        max_length=128,
        description="Plaintext password to be hashed before storage.",
    )


class UserUpdate(BaseModel):
    """
    Schema for updating an existing user (partial update).
    All fields are optional.
    """

    username: Optional[str] = Field(default=None, min_length=1, max_length=64)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(default=None, max_length=128)
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    tenant_id: Optional[int] = None
    password: Optional[str] = Field(
        default=None,
        min_length=6,
        max_length=128,
        description="New password to set (if changing).",
    )

    class Config:
        orm_mode = True


class UserRead(UserBase):
    """
    Schema for reading/returning user objects from the API.
    """

    id: int = Field(..., description="Primary key of the user record.")

    class Config:
        orm_mode = True
