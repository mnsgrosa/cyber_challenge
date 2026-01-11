from typing import Dict, Optional

from pydantic import BaseModel, Field


class Governance(BaseModel):
    username: str = Field(..., description="Username or email from user")
    password: str = Field(..., description="Password for data access")


class GovernanceResponse(BaseModel):
    token: str = Field(..., description="UUid str for user access")


class AgentRequest(BaseModel):
    prompt: str = Field(..., description="Prompt for the agent supervisor")


class AgentResponse(BaseModel):
    content: str = Field(..., description="Agent answer")
    data: Optional[Dict[str, int]] = Field(None, description="Chart data")
