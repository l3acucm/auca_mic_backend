import re

# E.164-ish: optional leading +, 7-15 digits, no leading zero.
_PHONE_RE = re.compile(r'^\+?[1-9]\d{6,14}$')


def validate_phone_number(value: str) -> bool:
    """Used by django-moses (MOSES['PHONE_NUMBER_VALIDATOR'])."""
    return bool(_PHONE_RE.match((value or '').strip()))
