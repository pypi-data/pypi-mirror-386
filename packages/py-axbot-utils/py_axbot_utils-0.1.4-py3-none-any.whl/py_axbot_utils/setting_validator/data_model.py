from py_axbot_utils.exceptions import ValidationError


class DataModel:
    fields = {}

    @classmethod
    def validate_object(cls, obj):
        # TODO: return all errors, not only the first one
        all_errors = {}

        for name, value in obj.items():
            field = cls.fields.get(name)
            if field:
                for validator in field.validators:
                    try:
                        validator(value)
                    except TypeError as e:
                        if not all_errors.get(name):
                            all_errors[name] = []
                        all_errors[name].append(e.args[0])
                        break
                    except ValidationError as e:
                        if not all_errors.get(name):
                            all_errors[name] = []
                        all_errors[name].extend(e.detail)

        if all_errors:
            raise ValidationError(all_errors)
