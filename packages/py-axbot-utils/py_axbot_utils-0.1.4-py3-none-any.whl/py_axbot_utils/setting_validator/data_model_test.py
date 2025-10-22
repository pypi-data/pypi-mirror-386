import pytest

from py_axbot_utils.setting_validator import DataModel
from py_axbot_utils.exceptions import ValidationError
from py_axbot_utils.fields import NumberField, EmailField


class MyModel(DataModel):
    fields = {
        "control.max_forward_velocity": NumberField(0, 2.0),
        "email": EmailField(),
    }


def test_number_field():
    MyModel.validate_object({"control.max_forward_velocity": 1.0})

    with pytest.raises(ValidationError) as e:
        MyModel.validate_object({"control.max_forward_velocity": "a"})
    assert e.value.detail == {
        "control.max_forward_velocity": [
            "'a' is not a number.",
        ],
    }

    with pytest.raises(ValidationError) as e:
        MyModel.validate_object(
            {
                "control.max_forward_velocity": 100,
                "email": "abc",
            }
        )
    assert e.value.detail == {
        "control.max_forward_velocity": [
            "Value '100' should not be larger than 2.0",
        ],
        "email": [
            "'abc' is not a valid email address",
        ],
    }
