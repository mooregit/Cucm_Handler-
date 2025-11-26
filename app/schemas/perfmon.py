from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from .common import CUCMBase


class PerfMonBase(CUCMBase):
    node: str = Field(..., example="cucm-pub")


class PerfMonCounterRequest(PerfMonBase):
    counters: List[str] = Field(
        ..., 
        example=[
            "Processor: % Processor Time",
            "Memory: Available MBytes"
        ]
    )


class PerfMonCounterValue(BaseModel):
    counter: str
    value: float
    units: Optional[str] = None
    timestamp: str


class PerfMonCounterResponse(BaseModel):
    node: str
    results: List[PerfMonCounterValue]


class PerfMonGroupListResponse(BaseModel):
    groups: List[str]