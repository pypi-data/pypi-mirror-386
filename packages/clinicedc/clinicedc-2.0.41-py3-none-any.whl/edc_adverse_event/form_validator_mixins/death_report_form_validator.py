from __future__ import annotations

from typing import TYPE_CHECKING, Any
from zoneinfo import ZoneInfo

from django import forms
from django.apps import apps as django_apps
from django.conf import settings

from edc_constants.constants import CLOSED, OTHER
from edc_form_validators.base_form_validator import INVALID_ERROR
from edc_utils.text import convert_php_dateformat

if TYPE_CHECKING:
    from datetime import date


class DeathReportFormValidatorMixin:
    """A form validator mixin for the Death Report form"""

    death_report_date_field = "death_datetime"
    study_day_field = "study_day"

    @property
    def cause_of_death_model_cls(self):
        return django_apps.get_model("edc_adverse_event.causeofdeath")

    def clean(self: Any) -> None:
        self.validate_study_day_with_death_report_date()

        self.date_is_after_or_raise(
            field="report_datetime",
            reference_value=self.death_report_date,
            inclusive=True,
            extra_msg="(on or after date of death)",
        )

        cause_of_death = self.cause_of_death_model_cls.objects.get(name=OTHER)

        self.validate_other_specify(
            field="cause_of_death",
            other_specify_field="cause_of_death_other",
            other_stored_value=cause_of_death.name,
        )

        self.required_if(
            CLOSED, field="report_status", field_required="report_closed_datetime"
        )

    @property
    def death_report_date(self: Any) -> date:
        try:
            return self.cleaned_data.get(self.death_report_date_field).date()
        except AttributeError:
            return self.cleaned_data.get(self.death_report_date_field)

    def validate_study_day_with_death_report_date(
        self: Any,
        subject_identifier: str | None = None,
    ) -> None:
        """Raises an exception if study day does not match
        calculation against ZoneInfo.

        Note: study-day is 1-based.

        This is skipped if `study_day_field` does not exist.
        """
        study_day = self.cleaned_data.get(self.study_day_field)
        if study_day is not None and self.death_report_date is not None:
            subject_identifier = (
                subject_identifier
                or self.cleaned_data.get("subject_identifier")
                or self.instance.subject_identifier
            )
            if not subject_identifier:
                raise ValueError(f"Subject identifier cannot be None. See {self!r}")
            registered_subject_model_cls = django_apps.get_model(
                "edc_registration.registeredsubject"
            )
            randomization_datetime = registered_subject_model_cls.objects.get(
                subject_identifier=subject_identifier
            ).randomization_datetime
            days_on_study = (self.death_report_date - randomization_datetime.date()).days
            if study_day - 1 != days_on_study:
                formatted_date = randomization_datetime.astimezone(
                    ZoneInfo(settings.TIME_ZONE)
                ).strftime(convert_php_dateformat(settings.DATETIME_FORMAT))
                message = {
                    self.study_day_field: (
                        f"Invalid. Expected {days_on_study + 1}. "
                        f"Subject was registered on {formatted_date}"
                    )
                }
                raise forms.ValidationError(message, code=INVALID_ERROR)
