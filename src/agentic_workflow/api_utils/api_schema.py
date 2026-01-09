from pydantic import BaseModel, Field


class Governance(BaseModel):
    username: str = Field(..., description="Username or email from user")
    password: str = Field(..., description="Password for data access")


class GovernanceResponse(BaseModel):
    token: str = Field(..., description="UUid str for user access")
