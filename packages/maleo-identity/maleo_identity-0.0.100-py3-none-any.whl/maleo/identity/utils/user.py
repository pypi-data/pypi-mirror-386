from typing import Literal, Type, overload
from ..dtos import (
    StandardUserDTO,
    FullUserDTO,
    AnyUserDTOType,
)
from ..schemas.common import (
    StandardUserSchema,
    FullUserSchema,
    AnyUserSchemaType,
)
from ..enums.user import Granularity


@overload
def get_dto_model(
    granularity: Literal[Granularity.STANDARD],
    /,
) -> Type[StandardUserDTO]: ...
@overload
def get_dto_model(
    granularity: Literal[Granularity.FULL],
    /,
) -> Type[FullUserDTO]: ...
@overload
def get_dto_model(
    granularity: Granularity = Granularity.STANDARD,
    /,
) -> AnyUserDTOType: ...
def get_dto_model(
    granularity: Granularity = Granularity.STANDARD,
    /,
) -> AnyUserDTOType:
    if granularity is Granularity.STANDARD:
        return StandardUserDTO
    elif granularity is Granularity.FULL:
        return FullUserDTO


@overload
def get_schema_model(
    granularity: Literal[Granularity.STANDARD],
    /,
) -> Type[StandardUserSchema]: ...
@overload
def get_schema_model(
    granularity: Literal[Granularity.FULL],
    /,
) -> Type[FullUserSchema]: ...
@overload
def get_schema_model(
    granularity: Granularity = Granularity.STANDARD,
    /,
) -> AnyUserSchemaType: ...
def get_schema_model(
    granularity: Granularity = Granularity.STANDARD,
    /,
) -> AnyUserSchemaType:
    if granularity is Granularity.STANDARD:
        return StandardUserSchema
    elif granularity is Granularity.FULL:
        return FullUserSchema
