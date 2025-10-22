import math
from py_axbot_utils.setting_validator import validator, validate
from py_axbot_utils.exceptions import ValidationError


def is_valid_number(value):
    return isinstance(value, (int, float)) and not math.isnan(value)


@validator("robot.footprint")
def validate_robot_footprint(value):
    def within_range(coord: float):
        return coord >= -5 and coord <= 5

    format_error = ValidationError(
        "footprint must be a two dimension array like [[-1, -1], [1, -1], [1, 1], [-1, 1]]"
    )

    if not isinstance(value, list):
        raise format_error
    for item in value:
        if not isinstance(item, list) or len(item) != 2:
            raise format_error
        if not is_valid_number(item[0]) or not is_valid_number(item[1]):
            raise format_error
        if not within_range(item[0]) or not within_range(item[1]):
            raise ValidationError(
                "Value in foot print is too large. They must be in [-5, 5]"
            )


def test_footprint():
    validate("robot.footprint", [[1, 2]])
