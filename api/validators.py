from django.core.exceptions import ValidationError


def greater_equal_than_zero(value):
    if value < 0:
        raise ValidationError("Value must be greater than zero.")
