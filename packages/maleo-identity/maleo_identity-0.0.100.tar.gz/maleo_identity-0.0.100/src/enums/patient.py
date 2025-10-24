from enum import StrEnum
from maleo.types.string import ListOfStrs


class IdentifierType(StrEnum):
    ID = "id"
    UUID = "uuid"
    ID_CARD = "id_card"
    PASSPORT = "passport"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]


class ExpandableField(StrEnum):
    GENDER = "gender"
    BLOOD_TYPE = "blood_type"


ListOfExpandableFields = list[ExpandableField]
OptListOfExpandableFields = ListOfExpandableFields | None
