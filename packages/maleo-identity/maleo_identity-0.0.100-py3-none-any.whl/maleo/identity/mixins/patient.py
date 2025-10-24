from pydantic import Field
from typing import Annotated, Generic
from maleo.schemas.mixins.identity import Passport as BasePassport
from maleo.types.string import OptStrT


class Passport(BasePassport, Generic[OptStrT]):
    passport: Annotated[OptStrT, Field(..., description="Passport", max_length=9)]
