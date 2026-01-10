from typing import List

from pydantic import BaseModel, Field


class VulnerabilityToolResponse(BaseModel):
    vulnerabilities: List[str] = Field(
        ...,
        description="Description of the vulnerability with device name, cve, category and description",
    )


class NvdToolResponse(BaseModel):
    descriptions: List[str] = Field(
        ...,
        description="List of CVEs description",
    )


class ListerToolResponse(BaseModel):
    list: List[str] = Field(
        ...,
        description="List of items",
    )
