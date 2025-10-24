from typing import Literal, Type, overload
from ..dtos import (
    StandardOrganizationDTO,
    FullOrganizationDTO,
    AnyOrganizationDTOType,
)
from ..schemas.common import (
    StandardOrganizationSchema,
    FullOrganizationSchema,
    AnyOrganizationSchemaType,
)
from ..enums.organization import Granularity


@overload
def get_dto_model(
    granularity: Literal[Granularity.STANDARD],
    /,
) -> Type[StandardOrganizationDTO]: ...
@overload
def get_dto_model(
    granularity: Literal[Granularity.FULL],
    /,
) -> Type[FullOrganizationDTO]: ...
@overload
def get_dto_model(
    granularity: Granularity = Granularity.STANDARD,
    /,
) -> AnyOrganizationDTOType: ...
def get_dto_model(
    granularity: Granularity = Granularity.STANDARD,
    /,
) -> AnyOrganizationDTOType:
    if granularity is Granularity.STANDARD:
        return StandardOrganizationDTO
    elif granularity is Granularity.FULL:
        return FullOrganizationDTO


@overload
def get_schema_model(
    granularity: Literal[Granularity.STANDARD],
    /,
) -> Type[StandardOrganizationSchema]: ...
@overload
def get_schema_model(
    granularity: Literal[Granularity.FULL],
    /,
) -> Type[FullOrganizationSchema]: ...
@overload
def get_schema_model(
    granularity: Granularity = Granularity.STANDARD,
    /,
) -> AnyOrganizationSchemaType: ...
def get_schema_model(
    granularity: Granularity = Granularity.STANDARD,
    /,
) -> AnyOrganizationSchemaType:
    if granularity is Granularity.STANDARD:
        return StandardOrganizationSchema
    elif granularity is Granularity.FULL:
        return FullOrganizationSchema
