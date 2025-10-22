from py_axbot_utils.translations import _


class ValidationError(Exception):
    default_detail = _("Invalid input.")

    def __init__(self, detail=None):
        if detail is None:
            detail = self.default_detail

        # For validation failures, we may collect many errors together,
        # so the details should always be coerced to a list if not already.
        if isinstance(detail, tuple):
            detail = list(detail)
        elif not isinstance(detail, dict) and not isinstance(detail, list):
            detail = [detail]

        self.detail = detail
