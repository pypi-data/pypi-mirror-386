from __future__ import annotations

from datetime import datetime


class ReportDatetimeModelFormMixin:
    # may also be appt_datetime or requisition_datetime
    report_datetime_field_attr: str = "report_datetime"

    @property
    def report_datetime(self) -> datetime | None:
        """Returns the report_datetime or None from
        cleaned_data.

        if key does not exist, returns the instance report_datetime.

        Django should raise a required field ValidationError before getting here
        if report_datetime is none.
        """
        report_datetime = None
        if self.report_datetime_field_attr in self.cleaned_data:
            report_datetime = self.cleaned_data.get(self.report_datetime_field_attr)
        elif self.instance:
            report_datetime = getattr(self.instance, self.report_datetime_field_attr)
        return report_datetime
