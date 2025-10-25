from pydantic import BaseModel, Field
from typing import Annotated, Generic
from maleo.types.boolean import OptBoolT
from maleo.types.misc import OptListOfAnyOrStrToAnyDict


class IsBidirectional(BaseModel, Generic[OptBoolT]):
    is_bidirectional: Annotated[OptBoolT, Field(..., description="Is Bidirectional")]


class Metadata(BaseModel):
    metadata: Annotated[
        OptListOfAnyOrStrToAnyDict, Field(None, description="Metadata")
    ] = None
