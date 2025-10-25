from pydantic import BaseModel, Field
from typing import Annotated


class APIKey(BaseModel):
    api_key: Annotated[str, Field(..., description="API Key", max_length=255)]
