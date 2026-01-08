from pydantic import BaseModel, Field


class Permissions(BaseModel):
    dashboard: bool = Field(...)
    management_page: bool = Field(...)
    crud: bool = Field(...)
    delete: bool = Field(...)


class Governance(BaseModel):
    username: str = Field(..., description="Username or email from user")
    password: str = Field(..., description="Password for data access")


class GovernanceResponse(BaseModel):
    token: str = Field(..., description="UUid str for user access")
