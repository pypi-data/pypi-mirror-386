from pydantic import BaseModel, Field
from typing import Annotated, Generic, Literal, TypeVar, overload
from uuid import UUID
from maleo.enums.organization import (
    OptOrganizationRelation,
    OrganizationType,
    OptOrganizationType,
    FullOrganizationTypeMixin,
    OptListOfOrganizationTypes,
    FullOrganizationTypesMixin,
)
from maleo.enums.status import (
    ListOfDataStatuses,
    FULL_DATA_STATUSES,
)
from maleo.schemas.mixins.filter import convert as convert_filter
from maleo.schemas.mixins.identity import (
    IdentifierTypeValue,
    Ids,
    UUIDs,
    Keys,
    Names,
)
from maleo.schemas.mixins.sort import convert as convert_sort
from maleo.schemas.parameter import (
    ReadSingleParameter as BaseReadSingleParameter,
    ReadPaginatedMultipleParameter,
    StatusUpdateParameter as BaseStatusUpdateParameter,
    DeleteSingleParameter as BaseDeleteSingleParameter,
)
from maleo.types.dict import StrToAnyDict
from maleo.types.integer import OptInt, OptListOfInts
from maleo.types.string import OptStr, OptListOfStrs
from maleo.types.uuid import OptListOfUUIDs
from ..enums.organization import IdentifierType, OptListOfExpandableFields
from ..mixins.organization import Key, Name
from ..types.organization import IdentifierValueType


class Expand(BaseModel):
    expand: Annotated[
        OptListOfExpandableFields, Field(None, description="Expand", min_length=1)
    ] = None


class CreateQuery(Expand):
    pass


class InsertData(Name[str], Key[str], FullOrganizationTypeMixin[OrganizationType]):
    pass


class CreateData(InsertData):
    related_to: Annotated[OptInt, Field(None, description="Related to", ge=1)] = None
    relation: Annotated[
        OptOrganizationRelation, Field(None, description="Relation")
    ] = None


class CreateParameter(CreateQuery, CreateData):
    pass


class ReadMultipleParameter(
    Expand,
    ReadPaginatedMultipleParameter,
    Names[OptListOfStrs],
    Keys[OptListOfStrs],
    FullOrganizationTypesMixin[OptListOfOrganizationTypes],
    UUIDs[OptListOfUUIDs],
    Ids[OptListOfInts],
):
    @property
    def _query_param_fields(self) -> set[str]:
        return {
            "ids",
            "uuids",
            "statuses",
            "organization_types",
            "keys",
            "names",
            "search",
            "page",
            "limit",
            "use_cache",
            "expand",
        }

    def to_query_params(self) -> StrToAnyDict:
        params = self.model_dump(
            mode="json", include=self._query_param_fields, exclude_none=True
        )
        params["filters"] = convert_filter(self.date_filters)
        params["sorts"] = convert_sort(self.sort_columns)
        params = {k: v for k, v in params.items()}
        return params


class ReadSingleParameter(
    Expand, BaseReadSingleParameter[IdentifierType, IdentifierValueType]
):
    @overload
    @classmethod
    def new(
        cls,
        identifier_type: Literal[IdentifierType.ID],
        identifier_value: int,
        statuses: ListOfDataStatuses = list(FULL_DATA_STATUSES),
        use_cache: bool = True,
        expand: OptListOfExpandableFields = None,
    ) -> "ReadSingleParameter": ...
    @overload
    @classmethod
    def new(
        cls,
        identifier_type: Literal[IdentifierType.UUID],
        identifier_value: UUID,
        statuses: ListOfDataStatuses = list(FULL_DATA_STATUSES),
        use_cache: bool = True,
        expand: OptListOfExpandableFields = None,
    ) -> "ReadSingleParameter": ...
    @overload
    @classmethod
    def new(
        cls,
        identifier_type: Literal[IdentifierType.KEY],
        identifier_value: str,
        statuses: ListOfDataStatuses = list(FULL_DATA_STATUSES),
        use_cache: bool = True,
        expand: OptListOfExpandableFields = None,
    ) -> "ReadSingleParameter": ...
    @classmethod
    def new(
        cls,
        identifier_type: IdentifierType,
        identifier_value: IdentifierValueType,
        statuses: ListOfDataStatuses = list(FULL_DATA_STATUSES),
        use_cache: bool = True,
        expand: OptListOfExpandableFields = None,
    ) -> "ReadSingleParameter":
        return cls(
            identifier_type=identifier_type,
            identifier_value=identifier_value,
            statuses=statuses,
            use_cache=use_cache,
            expand=expand,
        )

    def to_query_params(self) -> StrToAnyDict:
        return self.model_dump(
            mode="json", include={"statuses", "use_cache", "expand"}, exclude_none=True
        )


class FullUpdateData(Name[str], Key[str], FullOrganizationTypeMixin[OrganizationType]):
    pass


class PartialUpdateData(
    Name[OptStr], Key[OptStr], FullOrganizationTypeMixin[OptOrganizationType]
):
    pass


UpdateDataT = TypeVar("UpdateDataT", FullUpdateData, PartialUpdateData)


class UpdateDataMixin(BaseModel, Generic[UpdateDataT]):
    data: UpdateDataT = Field(..., description="Update data")


class UpdateParameter(
    Expand,
    UpdateDataMixin[UpdateDataT],
    IdentifierTypeValue[
        IdentifierType,
        IdentifierValueType,
    ],
    Generic[UpdateDataT],
):
    pass


class StatusUpdateParameter(
    Expand,
    BaseStatusUpdateParameter[IdentifierType, IdentifierValueType],
):
    pass


class DeleteSingleParameter(
    BaseDeleteSingleParameter[IdentifierType, IdentifierValueType]
):
    pass
