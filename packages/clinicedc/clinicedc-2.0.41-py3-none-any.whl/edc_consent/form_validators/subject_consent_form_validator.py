from __future__ import annotations

from datetime import datetime
from typing import Any

from django.conf import settings

from edc_form_validators import INVALID_ERROR
from edc_screening.form_validator_mixins import SubjectScreeningFormValidatorMixin
from edc_sites.site import sites
from edc_utils import AgeValueError, age
from edc_utils.date import to_local
from edc_utils.text import convert_php_dateformat

from ..site_consents import site_consents


class SubjectConsentFormValidatorMixin(SubjectScreeningFormValidatorMixin):
    """Form Validator mixin for the consent model."""

    def __init__(self: Any, **kwargs):
        super().__init__(**kwargs)
        self._consent_datetime = None

    def _clean(self) -> None:
        self.validate_demographics()
        super()._clean()

    def validate_demographics(self) -> None:
        self.validate_consent_datetime()
        self.validate_age()
        self.validate_gender()
        self.validate_identity()

    @property
    def gender(self):
        return self.cleaned_data.get("gender")

    @property
    def dob(self):
        return self.cleaned_data.get("dob")

    @property
    def guardian_name(self):
        return self.cleaned_data.get("guardian_name")

    @property
    def consent_model(self):
        return settings.SUBJECT_CONSENT_MODEL

    @property
    def consent_model_cls(self):
        cdef = site_consents.get_consent_definition(
            model=self.consent_model, site=sites.get(self.instance.site.id)
        )
        return cdef.model_cls

    @property
    def consent_datetime(self) -> datetime | None:
        if not self._consent_datetime:
            if "consent_datetime" in self.cleaned_data:
                if self.add_form and not self.cleaned_data.get("consent_datetime"):
                    self.raise_validation_error(
                        {"consent_datetime": "This field is required."}, INVALID_ERROR
                    )
                self._consent_datetime = self.cleaned_data.get("consent_datetime")
            else:
                self._consent_datetime = self.instance.consent_datetime
        return self._consent_datetime

    @property
    def screening_age_in_years(self) -> int:
        """Returns age in years calculated from dob relative to
        screening datetime"""
        try:
            rdelta = age(self.dob, self.subject_screening.report_datetime.date())
        except AgeValueError as e:
            self.raise_validation_error(str(e), INVALID_ERROR, exc=e)
        return rdelta.years

    def validate_age(self) -> None:
        """Validate age matches that on the screening form."""
        if self.dob and self.screening_age_in_years != self.subject_screening.age_in_years:
            self.raise_validation_error(
                {
                    "dob": "Age mismatch. The date of birth entered does "
                    f"not match the age at screening. "
                    f"Expected {self.subject_screening.age_in_years}. "
                    f"Got {self.screening_age_in_years}."
                },
                INVALID_ERROR,
            )

    def validate_gender(self) -> None:
        """Validate gender matches that on the screening form."""
        if self.gender != self.subject_screening.gender:
            self.raise_validation_error(
                {
                    "gender": "Gender mismatch. The gender entered does "
                    f"not match that reported at screening. "
                    f"Expected '{self.subject_screening.get_gender_display()}'. "
                    f"Got `{self.gender}`."
                },
                INVALID_ERROR,
            )

    def validate_consent_datetime(self) -> None:
        """Validate consent datetime with the eligibility datetime.

        Eligibility datetime must come first.

        Watchout for timezone, cleaned_data has local TZ.
        """
        if not self.subject_screening.eligibility_datetime:
            self.raise_validation_error(
                (
                    "Unable to determine the eligibility datetime from the "
                    f"screening form. See {self.subject_screening._meta.verbose_name}"
                    f"({self.subject_screening}). Got None."
                ),
                INVALID_ERROR,
            )
        if self.consent_datetime:
            if (
                self.consent_datetime - self.subject_screening.eligibility_datetime
            ).total_seconds() < 0:
                dt_str = to_local(self.subject_screening.eligibility_datetime).strftime(
                    convert_php_dateformat(settings.SHORT_DATETIME_FORMAT)
                )
                self.raise_validation_error(
                    {
                        "consent_datetime": (
                            f"Cannot be before the date and time eligibility "
                            f"was confirmed. Eligibility was confirmed at "
                            f"{dt_str}."
                        )
                    },
                    INVALID_ERROR,
                )

    def validate_identity(self: Any) -> None:
        pass
