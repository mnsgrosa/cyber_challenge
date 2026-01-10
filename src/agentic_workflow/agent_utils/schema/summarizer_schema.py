# TODO: Add the agent schemas for a more precise return from each agent

from datetime import date
from typing import Any, Dict, List

from pandas._config.config import describe_option
from pydantic import BaseModel, Field


class Vulnerability(BaseModel):
    name: str = Field(..., description="Device name")
    description: str = Field(..., description="Vulnerability description")
    cve: str = Field(..., description="Common Vulnerabilities and Exposures identifier")
    discovery_date: date = Field(..., description="Vulnerability date of discovery")


class VulnerabilityToolResponse(BaseModel):
    vulnerabilities: List[Vulnerability]
