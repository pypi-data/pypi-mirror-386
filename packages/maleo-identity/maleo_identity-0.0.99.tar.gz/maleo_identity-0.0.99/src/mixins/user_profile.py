from pydantic import BaseModel, Field
from typing import Annotated, Generic
from maleo.types.string import OptStrT


class LeadingTitle(BaseModel, Generic[OptStrT]):
    leading_title: Annotated[
        OptStrT, Field(..., description="User's Leading Title", max_length=25)
    ]


class FirstName(BaseModel, Generic[OptStrT]):
    first_name: Annotated[
        OptStrT, Field(..., description="User's First Name", max_length=50)
    ]


class MiddleName(BaseModel, Generic[OptStrT]):
    middle_name: Annotated[
        OptStrT, Field(..., description="User's Middle Name", max_length=50)
    ]


class LastName(BaseModel, Generic[OptStrT]):
    last_name: Annotated[
        OptStrT, Field(..., description="User's Last Name", max_length=50)
    ]


class EndingTitle(BaseModel, Generic[OptStrT]):
    ending_title: Annotated[
        OptStrT, Field(..., description="User's Ending Title", max_length=25)
    ]


class AvatarName(BaseModel, Generic[OptStrT]):
    avatar_name: Annotated[OptStrT, Field(..., description="User's Avatar Name")]


class AvatarUrl(BaseModel, Generic[OptStrT]):
    avatar_url: Annotated[OptStrT, Field(..., description="User's Avatar URL")]
