from pydantic import BaseModel, Field
from typing import Annotated, Generic, Literal, TypeVar, overload
from uuid import UUID
from maleo.enums.status import (
    ListOfDataStatuses,
    FULL_DATA_STATUSES,
)
from maleo.enums.user import (
    UserType,
    OptUserType,
    FullUserTypeMixin,
    OptListOfUserTypes,
    FullUserTypesMixin,
)
from maleo.schemas.mixins.filter import convert as convert_filter
from maleo.schemas.mixins.identity import (
    IdentifierTypeValue,
    Ids,
    UUIDs,
    IntOrganizationIds,
)
from maleo.schemas.mixins.sort import convert as convert_sort
from maleo.schemas.parameter import (
    ReadSingleParameter as BaseReadSingleParameter,
    ReadPaginatedMultipleParameter,
    StatusUpdateParameter as BaseStatusUpdateParameter,
    DeleteSingleParameter as BaseDeleteSingleParameter,
)
from maleo.types.dict import StrToAnyDict
from maleo.types.integer import OptListOfInts
from maleo.types.string import OptStr, OptListOfStrs
from maleo.types.uuid import OptListOfUUIDs
from ..enums.user import IdentifierType, OptListOfExpandableFields
from ..mixins.user import (
    Username,
    Usernames,
    Email,
    Emails,
    Phone,
    Phones,
)
from ..types.user import IdentifierValueType


class Expand(BaseModel):
    expand: Annotated[
        OptListOfExpandableFields, Field(None, description="Expand", min_length=1)
    ] = None


class CreateParameter(
    Phone[str], Email[str], Username[str], FullUserTypeMixin[UserType]
):
    pass


class ReadMultipleParameter(
    Expand,
    ReadPaginatedMultipleParameter,
    Phones[OptListOfStrs],
    Emails[OptListOfStrs],
    Usernames[OptListOfStrs],
    FullUserTypesMixin[OptListOfUserTypes],
    UUIDs[OptListOfUUIDs],
    Ids[OptListOfInts],
    IntOrganizationIds[OptListOfInts],
):
    @property
    def _query_param_fields(self) -> set[str]:
        return {
            "organization_ids",
            "ids",
            "uuids",
            "statuses",
            "user_types",
            "usernames",
            "emails",
            "phones",
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
    ) -> "ReadSingleParameter": ...
    @overload
    @classmethod
    def new(
        cls,
        identifier_type: Literal[IdentifierType.UUID],
        identifier_value: UUID,
        statuses: ListOfDataStatuses = list(FULL_DATA_STATUSES),
        use_cache: bool = True,
    ) -> "ReadSingleParameter": ...
    @overload
    @classmethod
    def new(
        cls,
        identifier_type: Literal[IdentifierType.USERNAME, IdentifierType.EMAIL],
        identifier_value: str,
        statuses: ListOfDataStatuses = list(FULL_DATA_STATUSES),
        use_cache: bool = True,
    ) -> "ReadSingleParameter": ...
    @classmethod
    def new(
        cls,
        identifier_type: IdentifierType,
        identifier_value: IdentifierValueType,
        statuses: ListOfDataStatuses = list(FULL_DATA_STATUSES),
        use_cache: bool = True,
    ) -> "ReadSingleParameter":
        return cls(
            identifier_type=identifier_type,
            identifier_value=identifier_value,
            statuses=statuses,
            use_cache=use_cache,
        )

    def to_query_params(self) -> StrToAnyDict:
        return self.model_dump(
            mode="json", include={"statuses", "use_cache", "expand"}, exclude_none=True
        )


class PasswordUpdateData(BaseModel):
    old: Annotated[str, Field(..., description="Old Password", max_length=255)]
    old_confirmation: Annotated[
        str, Field(..., description="Old Password Confirmation", max_length=255)
    ]
    new: Annotated[str, Field(..., description="New Password", max_length=255)]


class FullUpdateData(
    Phone[str], Email[str], Username[str], FullUserTypeMixin[UserType]
):
    pass


class PartialUpdateData(
    Phone[OptStr], Email[OptStr], Username[OptStr], FullUserTypeMixin[OptUserType]
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
