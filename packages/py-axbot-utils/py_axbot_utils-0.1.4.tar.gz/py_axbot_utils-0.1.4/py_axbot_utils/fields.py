from .validators import RangeValidator, NumberValidator, StringValidator, EmailValidator


class Field:
    def __init__(self, default=None) -> None:
        self.default = default
        self.validators = []


class NumberField(Field):
    def __init__(self, min_value=None, max_value=None, default=None) -> None:
        super().__init__(default)

        self.validators.append(NumberValidator())
        self.validators.append(RangeValidator(min_value, max_value))


class StringField(Field):
    def __init__(self, default=None) -> None:
        super().__init__(default)

        self.validators.append(StringValidator())


class EmailField(StringField):
    def __init__(self, default=None) -> None:
        super().__init__(default)

        self.validators.append(EmailValidator())
