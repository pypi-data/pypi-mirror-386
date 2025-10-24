from pydantic import BaseModel, Field
from typing import Annotated, Generic, Literal, TypeVar, overload
from uuid import UUID
from maleo.enums.identity import (
    OptBloodType,
    BloodTypeMixin,
    OptListOfBloodTypes,
    BloodTypesMixin,
    OptGender,
    GenderMixin,
    OptListOfGenders,
    GendersMixin,
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
    IntUserId,
    IntOrganizationIds,
    BirthDate,
)
from maleo.schemas.mixins.sort import convert as convert_sort
from maleo.schemas.parameter import (
    ReadSingleParameter as BaseReadSingleParameter,
    ReadPaginatedMultipleParameter,
    StatusUpdateParameter as BaseStatusUpdateParameter,
    DeleteSingleParameter as BaseDeleteSingleParameter,
)
from maleo.types.datetime import OptDate
from maleo.types.dict import StrToAnyDict
from maleo.types.integer import OptListOfInts
from maleo.types.string import OptStr
from maleo.types.uuid import OptListOfUUIDs
from ..enums.user_profile import IdentifierType, OptListOfExpandableFields
from ..mixins.common import (
    IdCard,
    FullName,
    BirthPlace,
)
from ..mixins.user_profile import (
    LeadingTitle,
    FirstName,
    MiddleName,
    LastName,
    EndingTitle,
    AvatarName,
)
from ..types.user_profile import IdentifierValueType


class Expand(BaseModel):
    expand: Annotated[
        OptListOfExpandableFields, Field(None, description="Expand", min_length=1)
    ] = None


class CoreCreateData(
    BloodTypeMixin[OptBloodType],
    GenderMixin[OptGender],
    BirthDate[OptDate],
    BirthPlace[OptStr],
    FullName[str],
    EndingTitle[OptStr],
    LastName[str],
    MiddleName[OptStr],
    FirstName[str],
    LeadingTitle[OptStr],
    IdCard[OptStr],
):
    pass


class EssentialData(
    AvatarName[str],
    BloodTypeMixin[OptBloodType],
    GenderMixin[OptGender],
    BirthDate[OptDate],
    BirthPlace[OptStr],
    FullName[str],
    EndingTitle[OptStr],
    LastName[str],
    MiddleName[OptStr],
    FirstName[str],
    LeadingTitle[OptStr],
    IdCard[OptStr],
):
    pass


class InsertData(
    EssentialData,
    IntUserId[int],
):
    pass


class CreateParameter(
    AvatarName[str],
    BloodTypeMixin[OptBloodType],
    GenderMixin[OptGender],
    BirthDate[OptDate],
    BirthPlace[OptStr],
    FullName[str],
    EndingTitle[OptStr],
    LastName[str],
    MiddleName[OptStr],
    FirstName[str],
    LeadingTitle[OptStr],
    IdCard[OptStr],
    IntUserId[int],
):
    pass


class ReadMultipleParameter(
    Expand,
    ReadPaginatedMultipleParameter,
    BloodTypesMixin[OptListOfBloodTypes],
    GendersMixin[OptListOfGenders],
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
            "genders",
            "blood_types",
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
        identifier_type: Literal[IdentifierType.ID, IdentifierType.USER_ID],
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
        identifier_type: Literal[IdentifierType.ID_CARD],
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


class FullUpdateData(
    BloodTypeMixin[OptBloodType],
    GenderMixin[OptGender],
    BirthDate[OptDate],
    BirthPlace[OptStr],
    EndingTitle[OptStr],
    LastName[str],
    MiddleName[OptStr],
    FirstName[str],
    LeadingTitle[OptStr],
    IdCard[OptStr],
):
    pass


class PartialUpdateData(
    BloodTypeMixin[OptBloodType],
    GenderMixin[OptGender],
    BirthDate[OptDate],
    BirthPlace[OptStr],
    EndingTitle[OptStr],
    LastName[OptStr],
    MiddleName[OptStr],
    FirstName[OptStr],
    LeadingTitle[OptStr],
    IdCard[OptStr],
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
