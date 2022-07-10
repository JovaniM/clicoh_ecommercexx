from api import enums
from django.core.exceptions import ValidationError


def greater_equal_than_zero(value):
    if value < 0:
        raise ValidationError(enums.Errors.GREATER_EQUAL_ZERO_ERROR.value)


def greater_than_zero(value):
    if value <= 0:
        raise ValidationError(enums.Errors.GREATER_ZERO_ERROR.value)
