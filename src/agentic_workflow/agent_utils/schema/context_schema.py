from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class ToolResponse(BaseModel):
    tool_name: str
    output: Any
    table_queried: Optional[str] = None
    input_params: Optional[dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    execution_id: Optional[str] = None
