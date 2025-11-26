from pydantic import BaseModel, Field
from typing import Optional


class StatusResponse(BaseModel):
    status: str = Field(..., example="success")
    message: Optional[str] = Field(None, example="Operation completed successfully.")


class CUCMBase(BaseModel):
    cucm_host: str = Field(..., example="10.10.20.1")
    cucm_username: str = Field(..., example="admin")
    cucm_password: str = Field(..., example="C1sco12345")