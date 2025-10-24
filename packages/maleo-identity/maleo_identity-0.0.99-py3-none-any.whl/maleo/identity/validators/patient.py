from maleo.types.string import OptStr


def validate_id_card_or_passport(id_card: OptStr, passport: OptStr):
    if id_card is None and passport is None:
        raise ValueError("Either ID Card and Passport must exist")
