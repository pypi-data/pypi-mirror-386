import contextlib
from typing import Any


def calculate_missing(obj: Any, panel: Any) -> tuple[int, str | None]:
    """Returns a tuple of (missing_count, missing)

    Counts the number of blank results within the model
    instance (missing_count).

    Creates a string of utest_ids of the missing field values
    (missing).

    Only for model classes whose field classes follow the naming
    convention tied to a lab panel.

    See also: BloodResultsMethodsModelMixin and
    BloodResultsFieldsModelMixin.
    """
    fields = [fld_cls.name for fld_cls in obj._meta.get_fields()]
    missing = []
    for utest_id in panel.utest_ids:
        for field in fields:
            with contextlib.suppress(ValueError):
                utest_id, _ = utest_id  # noqa: PLW2901
            if field == utest_id or (
                field == f"{utest_id}_value" and getattr(obj, field) is None
            ):
                missing.append(field)
    return len(missing), ",".join(missing) if missing else ""
