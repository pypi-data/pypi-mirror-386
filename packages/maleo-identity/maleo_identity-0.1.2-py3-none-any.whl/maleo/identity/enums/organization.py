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
    KEY = "key"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]


class ExpandableField(StrEnum):
    ORGANIZATION_TYPE = "organization_type"


ListOfExpandableFields = list[ExpandableField]
OptListOfExpandableFields = ListOfExpandableFields | None
