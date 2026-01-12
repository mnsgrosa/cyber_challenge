from typing import List

from pydantic import BaseModel, Field


class RetrievalResponse(BaseModel):
    list: List[str] = Field(
        ...,
        description="Condensed list of string with information differs a bit from each tool",
    )
