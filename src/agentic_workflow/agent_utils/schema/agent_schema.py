# TODO: Add the agent schemas for a more precise return from each agent

from pydantic import BaseModel, Field


class NvdSearchResponse(BaseModel):
    id: str = Field(..., description="Vulnerability code")
    description: str = Field(..., description="Vulnerability description")
