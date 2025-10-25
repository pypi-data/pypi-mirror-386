from datetime import date
from pydantic import BaseModel, Field, model_validator
from typing import Annotated, Generic, Self, TypeVar, Type
from maleo.enums.identity import OptRhesus, RhesusMixin
from maleo.metadata.schemas.organization_role import (
    FullOrganizationRoleMixin,
    KeyOrStandardSchema as KeyOrStandardOrganizationRoleSchema,
)
from maleo.enums.status import DataStatus as DataStatusEnum, SimpleDataStatusMixin
from maleo.metadata.schemas.blood_type import (
    FullBloodTypeMixin,
    OptKeyOrStandardSchema as OptKeyOrStandardBloodTypeSchema,
)
from maleo.metadata.schemas.gender import (
    FullGenderMixin,
    KeyOrStandardSchema as KeyOrStandardGenderSchema,
    OptKeyOrStandardSchema as OptKeyOrStandardGenderSchema,
)
from maleo.metadata.schemas.medical_role import (
    FullMedicalRoleMixin,
    KeyOrStandardSchema as KeyOrStandardMedicalRoleSchema,
)
from maleo.metadata.schemas.organization_type import (
    FullOrganizationTypeMixin,
    KeyOrStandardSchema as KeyOrStandardOrganizationTypeSchema,
)
from maleo.metadata.schemas.system_role import (
    FullSystemRoleMixin,
    KeyOrStandardSchema as KeyOrStandardSystemRoleSchema,
)
from maleo.metadata.schemas.user_type import (
    FullUserTypeMixin,
    KeyOrStandardSchema as KeyOrStandardUserTypeSchema,
)
from maleo.schemas.mixins.identity import (
    DataIdentifier,
    IntOrganizationId,
    IntUserId,
    BirthDate,
    DateOfBirth,
    IntSourceId,
    IntTargetId,
)
from maleo.schemas.mixins.timestamp import DataTimestamp
from maleo.types.datetime import OptDate
from maleo.types.integer import OptInt
from maleo.types.string import OptStr
from ..mixins.common import IdCard, FullName, BirthPlace, PlaceOfBirth
from ..mixins.api_key import APIKey
from ..mixins.organization_registration_code import Code, MaxUses, CurrentUses
from ..mixins.organization_relation import IsBidirectional, Metadata
from ..mixins.organization import Key as OrganizationKey, Name as OrganizationName
from ..mixins.patient import Passport
from ..mixins.user_profile import (
    LeadingTitle,
    FirstName,
    MiddleName,
    LastName,
    EndingTitle,
    AvatarUrl,
)
from ..mixins.user import Username, Email, Phone
from ..validators.patient import validate_id_card_or_passport


class APIKeySchema(
    APIKey,
    IntOrganizationId[OptInt],
    IntUserId[int],
    SimpleDataStatusMixin[DataStatusEnum],
    DataTimestamp,
    DataIdentifier,
):
    pass


class PatientSchema(
    RhesusMixin[OptRhesus],
    FullBloodTypeMixin[OptKeyOrStandardBloodTypeSchema],
    FullGenderMixin[KeyOrStandardGenderSchema],
    DateOfBirth[date],
    PlaceOfBirth[OptStr],
    FullName[str],
    Passport[OptStr],
    IdCard[OptStr],
    IntOrganizationId[int],
    SimpleDataStatusMixin[DataStatusEnum],
    DataTimestamp,
    DataIdentifier,
):
    @model_validator(mode="after")
    def chk_id_card_or_passport(self) -> Self:
        validate_id_card_or_passport(self.id_card, self.passport)
        return self


class OrganizationRegistrationCodeSchema(
    CurrentUses,
    MaxUses[int],
    Code[str],
    IntOrganizationId[int],
    SimpleDataStatusMixin[DataStatusEnum],
    DataTimestamp,
    DataIdentifier,
):
    pass


OptOrganizationRegistrationCodeSchema = OrganizationRegistrationCodeSchema | None


class OrganizationRegistrationCodeSchemaMixin(BaseModel):
    registration_code: Annotated[
        OptOrganizationRegistrationCodeSchema,
        Field(None, description="Organization's registration code"),
    ] = None


class StandardOrganizationSchema(
    OrganizationName[str],
    OrganizationKey[str],
    FullOrganizationTypeMixin[KeyOrStandardOrganizationTypeSchema],
    SimpleDataStatusMixin[DataStatusEnum],
    DataTimestamp,
    DataIdentifier,
):
    pass


class SourceOrganizationSchemaMixin(BaseModel):
    source: Annotated[
        StandardOrganizationSchema, Field(..., description="Source organization")
    ]


class TargetOrganizationSchemaMixin(BaseModel):
    target: Annotated[
        StandardOrganizationSchema, Field(..., description="Target organization")
    ]


class OrganizationRelationSchema(
    Metadata,
    IsBidirectional[bool],
    TargetOrganizationSchemaMixin,
    IntTargetId[int],
    SourceOrganizationSchemaMixin,
    IntSourceId[int],
    SimpleDataStatusMixin[DataStatusEnum],
    DataTimestamp,
    DataIdentifier,
):
    pass


class OrganizationRelationsSchemaMixin(BaseModel):
    relations: Annotated[
        list[OrganizationRelationSchema],
        Field(list[OrganizationRelationSchema](), description="Relations"),
    ] = list[OrganizationRelationSchema]()


class FullOrganizationSchema(
    OrganizationRegistrationCodeSchemaMixin,
    StandardOrganizationSchema,
):
    pass


AnyOrganizationSchemaType = (
    Type[StandardOrganizationSchema] | Type[FullOrganizationSchema]
)
AnyOrganizationSchema = StandardOrganizationSchema | FullOrganizationSchema
AnyOrganizationSchemaT = TypeVar("AnyOrganizationSchemaT", bound=AnyOrganizationSchema)


class OrganizationSchemaMixin(BaseModel, Generic[AnyOrganizationSchemaT]):
    organization: Annotated[
        AnyOrganizationSchemaT, Field(..., description="Organization")
    ]


class UserMedicalRoleSchema(
    FullMedicalRoleMixin[KeyOrStandardMedicalRoleSchema],
    IntOrganizationId[int],
    IntUserId[int],
    SimpleDataStatusMixin[DataStatusEnum],
    DataTimestamp,
    DataIdentifier,
):
    pass


class UserMedicalRolesSchemaMixin(BaseModel):
    medical_roles: Annotated[
        list[UserMedicalRoleSchema],
        Field(list[UserMedicalRoleSchema](), description="Medical roles"),
    ] = list[UserMedicalRoleSchema]()


class UserOrganizationRoleSchema(
    FullOrganizationRoleMixin[KeyOrStandardOrganizationRoleSchema],
    IntOrganizationId[int],
    IntUserId[int],
    SimpleDataStatusMixin[DataStatusEnum],
    DataTimestamp,
    DataIdentifier,
):
    pass


class UserOrganizationRolesSchemaMixin(BaseModel):
    organization_roles: Annotated[
        list[UserOrganizationRoleSchema],
        Field(list[UserOrganizationRoleSchema](), description="Organization roles"),
    ] = list[UserOrganizationRoleSchema]()


class UserProfileSchema(
    AvatarUrl[str],
    FullBloodTypeMixin[OptKeyOrStandardBloodTypeSchema],
    FullGenderMixin[OptKeyOrStandardGenderSchema],
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
    SimpleDataStatusMixin[DataStatusEnum],
    DataTimestamp,
    DataIdentifier,
):
    pass


OptUserProfileSchema = UserProfileSchema | None


class UserProfileSchemaMixin(BaseModel):
    profile: Annotated[
        OptUserProfileSchema, Field(None, description="User's Profile")
    ] = None


class UserSystemRoleSchema(
    FullSystemRoleMixin[KeyOrStandardSystemRoleSchema],
    IntUserId[int],
    SimpleDataStatusMixin[DataStatusEnum],
    DataTimestamp,
    DataIdentifier,
):
    pass


class UserSystemRolesSchemaMixin(BaseModel):
    system_roles: Annotated[
        list[UserSystemRoleSchema],
        Field(
            list[UserSystemRoleSchema](),
            description="User's system roles",
            min_length=1,
        ),
    ] = list[UserSystemRoleSchema]()


class StandardUserSchema(
    UserProfileSchemaMixin,
    Phone[str],
    Email[str],
    Username[str],
    FullUserTypeMixin[KeyOrStandardUserTypeSchema],
    SimpleDataStatusMixin[DataStatusEnum],
    DataTimestamp,
    DataIdentifier,
):
    pass


class UserOrganizationSchema(
    UserMedicalRolesSchemaMixin,
    UserOrganizationRolesSchemaMixin,
    OrganizationSchemaMixin[StandardOrganizationSchema],
    SimpleDataStatusMixin[DataStatusEnum],
    DataTimestamp,
    DataIdentifier,
):
    pass


class UserOrganizationsSchemaMixin(BaseModel):
    organizations: Annotated[
        list[UserOrganizationSchema],
        Field(list[UserOrganizationSchema](), description="Organizations"),
    ] = list[UserOrganizationSchema]()


class FullUserSchema(UserSystemRolesSchemaMixin, StandardUserSchema):
    pass


AnyUserSchemaType = Type[StandardUserSchema] | Type[FullUserSchema]
AnyUserSchema = StandardUserSchema | FullUserSchema
AnyUserSchemaT = TypeVar("AnyUserSchemaT", bound=AnyUserSchema)


class UserSchemaMixin(BaseModel, Generic[AnyUserSchemaT]):
    user: Annotated[AnyUserSchemaT, Field(..., description="User")]


class UserAndOrganizationSchema(
    UserMedicalRolesSchemaMixin,
    UserOrganizationRolesSchemaMixin,
    OrganizationSchemaMixin[StandardOrganizationSchema],
    UserSchemaMixin[StandardUserSchema],
    SimpleDataStatusMixin[DataStatusEnum],
    DataTimestamp,
    DataIdentifier,
):
    pass
