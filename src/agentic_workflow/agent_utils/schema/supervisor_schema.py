from typing import Dict, Optional

from pydantic import BaseModel, Field


class ApiResponse(BaseModel):
    tool_called: str = Field(..., description="Name from tool called")
    data_points: Optional[Dict[str, int]] = Field(
        ..., description="Dict with data points"
    )
    content: str = Field(..., description="Agent answer")
