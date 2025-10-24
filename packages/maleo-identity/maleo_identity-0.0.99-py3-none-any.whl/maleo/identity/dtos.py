from datetime import date
from pydantic import BaseModel, Field, model_validator
from typing import Annotated, Generic, Self, TypeVar, Type
from maleo.enums.identity import (
    OptBloodType,
    BloodTypeMixin,
    OptRhesus,
    RhesusMixin,
    Gender,
    OptGender,
    GenderMixin,
)
from maleo.enums.medical import MedicalRole, FullMedicalRoleMixin
from maleo.enums.organization import (
    OrganizationRole,
    FullOrganizationRoleMixin,
    OrganizationType,
    FullOrganizationTypeMixin,
)
from maleo.enums.status import DataStatus as DataStatusEnum, SimpleDataStatusMixin
from maleo.enums.system import SystemRole, FullSystemRoleMixin
from maleo.enums.user import UserType, FullUserTypeMixin
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
from maleo.types.string import OptStr
from .mixins.common import IdCard, FullName, BirthPlace, PlaceOfBirth
from .mixins.organization_registration_code import Code, MaxUses, CurrentUses
from .mixins.organization_relation import IsBidirectional, Metadata
from .mixins.organization import Key as OrganizationKey, Name as OrganizationName
from .mixins.patient import Passport
from .mixins.user_profile import (
    LeadingTitle,
    FirstName,
    MiddleName,
    LastName,
    EndingTitle,
    AvatarName,
)
from .mixins.user import Username, Email, Phone
from .validators.patient import validate_id_card_or_passport


class PatientDTO(
    RhesusMixin[OptRhesus],
    BloodTypeMixin[OptBloodType],
    GenderMixin[Gender],
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


class OrganizationRegistrationCodeDTO(
    CurrentUses,
    MaxUses[int],
    Code[str],
    IntOrganizationId[int],
    SimpleDataStatusMixin[DataStatusEnum],
    DataTimestamp,
    DataIdentifier,
):
    pass


OptOrganizationRegistrationCodeDTO = OrganizationRegistrationCodeDTO | None


class OrganizationRegistrationCodeDTOMixin(BaseModel):
    registration_code: Annotated[
        OptOrganizationRegistrationCodeDTO,
        Field(None, description="Organization's registration code"),
    ] = None


class StandardOrganizationDTO(
    OrganizationName[str],
    OrganizationKey[str],
    FullOrganizationTypeMixin[OrganizationType],
    SimpleDataStatusMixin[DataStatusEnum],
    DataTimestamp,
    DataIdentifier,
):
    pass


class SourceOrganizationDTOMixin(BaseModel):
    source: Annotated[
        StandardOrganizationDTO, Field(..., description="Source organization")
    ]


class TargetOrganizationDTOMixin(BaseModel):
    target: Annotated[
        StandardOrganizationDTO, Field(..., description="Target organization")
    ]


class OrganizationRelationDTO(
    Metadata,
    IsBidirectional[bool],
    TargetOrganizationDTOMixin,
    IntTargetId[int],
    SourceOrganizationDTOMixin,
    IntSourceId[int],
    SimpleDataStatusMixin[DataStatusEnum],
    DataTimestamp,
    DataIdentifier,
):
    pass


class OrganizationRelationsDTOMixin(BaseModel):
    relations: Annotated[
        list[OrganizationRelationDTO],
        Field(list[OrganizationRelationDTO](), description="Relations"),
    ] = list[OrganizationRelationDTO]()


class FullOrganizationDTO(
    OrganizationRelationsDTOMixin,
    OrganizationRegistrationCodeDTOMixin,
    StandardOrganizationDTO,
):
    pass


AnyOrganizationDTOType = Type[StandardOrganizationDTO] | Type[FullOrganizationDTO]
AnyOrganizationDTO = StandardOrganizationDTO | FullOrganizationDTO
AnyOrganizationDTOT = TypeVar("AnyOrganizationDTOT", bound=AnyOrganizationDTO)


class OrganizationDTOMixin(BaseModel, Generic[AnyOrganizationDTOT]):
    organization: Annotated[AnyOrganizationDTOT, Field(..., description="Organization")]


class UserMedicalRoleDTO(
    FullMedicalRoleMixin[MedicalRole],
    IntOrganizationId[int],
    IntUserId[int],
    SimpleDataStatusMixin[DataStatusEnum],
    DataTimestamp,
    DataIdentifier,
):
    pass


class UserMedicalRolesDTOMixin(BaseModel):
    medical_roles: Annotated[
        list[UserMedicalRoleDTO],
        Field(list[UserMedicalRoleDTO](), description="Medical roles"),
    ] = list[UserMedicalRoleDTO]()


class UserOrganizationRoleDTO(
    FullOrganizationRoleMixin[OrganizationRole],
    IntOrganizationId[int],
    IntUserId[int],
    SimpleDataStatusMixin[DataStatusEnum],
    DataTimestamp,
    DataIdentifier,
):
    pass


class UserOrganizationRolesDTOMixin(BaseModel):
    organization_roles: Annotated[
        list[UserOrganizationRoleDTO],
        Field(list[UserOrganizationRoleDTO](), description="Organization roles"),
    ] = list[UserOrganizationRoleDTO]()


class UserProfileDTO(
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
    SimpleDataStatusMixin[DataStatusEnum],
    DataTimestamp,
    DataIdentifier,
):
    pass


OptUserProfileDTO = UserProfileDTO | None


class UserProfileDTOMixin(BaseModel):
    profile: Annotated[OptUserProfileDTO, Field(None, description="User's Profile")] = (
        None
    )


class UserSystemRoleDTO(
    FullSystemRoleMixin[SystemRole],
    IntUserId[int],
    SimpleDataStatusMixin[DataStatusEnum],
    DataTimestamp,
    DataIdentifier,
):
    pass


class UserSystemRolesDTOMixin(BaseModel):
    system_roles: Annotated[
        list[UserSystemRoleDTO],
        Field(
            list[UserSystemRoleDTO](),
            description="User's system roles",
            min_length=1,
        ),
    ] = list[UserSystemRoleDTO]()


class StandardUserDTO(
    UserProfileDTOMixin,
    Phone[str],
    Email[str],
    Username[str],
    FullUserTypeMixin[UserType],
    SimpleDataStatusMixin[DataStatusEnum],
    DataTimestamp,
    DataIdentifier,
):
    pass


class UserOrganizationDTO(
    UserMedicalRolesDTOMixin,
    UserOrganizationRolesDTOMixin,
    OrganizationDTOMixin[StandardOrganizationDTO],
    SimpleDataStatusMixin[DataStatusEnum],
    DataTimestamp,
    DataIdentifier,
):
    pass


class UserOrganizationsDTOMixin(BaseModel):
    organizations: Annotated[
        list[UserOrganizationDTO],
        Field(list[UserOrganizationDTO](), description="Organizations"),
    ] = list[UserOrganizationDTO]()


class FullUserDTO(UserOrganizationsDTOMixin, StandardUserDTO):
    pass


AnyUserDTOType = Type[StandardUserDTO] | Type[FullUserDTO]
AnyUserDTO = StandardUserDTO | FullUserDTO
AnyUserDTOT = TypeVar("AnyUserDTOT", bound=AnyUserDTO)


class UserDTOMixin(BaseModel, Generic[AnyUserDTOT]):
    user: Annotated[AnyUserDTOT, Field(..., description="User")]


class UserAndOrganizationDTO(
    UserMedicalRolesDTOMixin,
    UserOrganizationRolesDTOMixin,
    OrganizationDTOMixin[StandardOrganizationDTO],
    UserDTOMixin[StandardUserDTO],
    SimpleDataStatusMixin[DataStatusEnum],
    DataTimestamp,
    DataIdentifier,
):
    pass
