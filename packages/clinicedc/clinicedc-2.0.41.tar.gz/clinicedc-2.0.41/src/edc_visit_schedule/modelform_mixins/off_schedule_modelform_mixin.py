from __future__ import annotations

from datetime import datetime

from django import forms

from ..subject_schedule import InvalidOffscheduleDate
from .visit_schedule_non_crf_modelform_mixin import VisitScheduleNonCrfModelFormMixin


class OffScheduleModelFormMixin(VisitScheduleNonCrfModelFormMixin):
    offschedule_datetime_field_attr = "offschedule_datetime"

    def clean(self):
        cleaned_data = super().clean()
        if self.offschedule_datetime:
            history_obj = self.schedule.history_model_cls.objects.get(
                subject_identifier=self.get_subject_identifier(),
                schedule_name=self.schedule_name,
                visit_schedule_name=self.visit_schedule_name,
            )
            try:
                self.schedule.subject(self.get_subject_identifier()).update_history_or_raise(
                    history_obj=history_obj,
                    offschedule_datetime=self.offschedule_datetime,
                    update=False,
                )
            except InvalidOffscheduleDate as e:
                raise forms.ValidationError(e) from e
            self.validate_visit_tracking_reports()
        return cleaned_data

    # TODO: validate_visit_tracking_reports before taking off schedule
    def validate_visit_tracking_reports(self):
        """Asserts that all visit tracking reports
        have been submitted.
        """
        pass

    @property
    def offschedule_datetime(self) -> datetime | None:
        if self.offschedule_datetime_field_attr in self.cleaned_data:
            return self.cleaned_data.get(self.offschedule_datetime_field_attr)
        return getattr(self.instance, self.offschedule_datetime_field_attr)

    @property
    def offschedule_compare_dates_as_datetimes(self):
        return True

    class Meta:
        help_text = {  # noqa: RUF012
            "subject_identifier": "(read-only)",
            "action_identifier": "(read-only)",
        }
        widgets = {  # noqa: RUF012
            "subject_identifier": forms.TextInput(attrs={"readonly": "readonly"}),
            "action_identifier": forms.TextInput(attrs={"readonly": "readonly"}),
        }
