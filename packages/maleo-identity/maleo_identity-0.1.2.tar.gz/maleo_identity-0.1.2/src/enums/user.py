from enum import StrEnum
from maleo.types.string import ListOfStrs


class Granularity(StrEnum):
    STANDARD = "standard"
    FULL = "full"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]


class IdentifierType(StrEnum):
    ID = "id"
    UUID = "uuid"
    USERNAME = "username"
    EMAIL = "email"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]


class ExpandableField(StrEnum):
    USER_TYPE = "user_type"
    GENDER = "gender"
    BLOOD_TYPE = "blood_type"
    SYSTEM_ROLE = "system_role"
    MEDICAL_ROLE = "medical_role"
    ORGANIZATION_ROLE = "organization_role"


ListOfExpandableFields = list[ExpandableField]
OptListOfExpandableFields = ListOfExpandableFields | None
