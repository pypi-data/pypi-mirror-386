import numbers
from email.utils import parseaddr

from .exceptions import ValidationError
from .translations import _


class NumberValidator:
    def __call__(self, value):
        if not isinstance(value, numbers.Number):
            raise TypeError(_("'{}' is not a number.").format(value))


class StringValidator:
    def __call__(self, value):
        if not isinstance(value, str):
            raise TypeError(_("{} is not a string.").format(value))


class RangeValidator:
    def __init__(self, min_value, max_value) -> None:
        self.min_value = min_value
        self.max_value = max_value

    def __call__(self, value):
        if self.min_value and value < self.min_value:
            raise ValidationError(
                _("Value '{}' should not be smaller than {}").format(
                    value, self.min_value
                )
            )

        if self.max_value and value > self.max_value:
            raise ValidationError(
                _("Value '{}' should not be larger than {}").format(
                    value, self.max_value
                )
            )


class EmailValidator:
    def __call__(self, value):
        _name, addr = parseaddr(value)
        if "@" not in addr:
            raise ValidationError(_("'{}' is not a valid email address").format(value))
