from django.db import models
from django.utils import timezone

from edc_constants.choices import YES_NO
from edc_constants.constants import NOT_APPLICABLE, YES
from edc_model.validators import date_not_future

from ...choices import AE_GRADE_SIMPLE, AE_OUTCOME
from ...utils import get_adverse_event_app_label


class AeFollowupFieldsModelMixin(models.Model):
    ae_initial = models.ForeignKey(
        f"{get_adverse_event_app_label()}.aeinitial", on_delete=models.PROTECT
    )

    report_datetime = models.DateTimeField(
        verbose_name="Report date and time", default=timezone.now
    )

    outcome = models.CharField(blank=False, null=False, max_length=25, choices=AE_OUTCOME)

    outcome_date = models.DateField(validators=[date_not_future])

    ae_grade = models.CharField(
        verbose_name="If severity increased, indicate grade",
        max_length=25,
        choices=AE_GRADE_SIMPLE,
        default=NOT_APPLICABLE,
    )

    relevant_history = models.TextField(
        verbose_name="Description summary of Adverse Event outcome",
        max_length=1000,
        blank=False,
        null=False,
        help_text="Indicate Adverse Event, clinical results,"
        "medications given, dosage,treatment plan and outcomes.",
    )

    followup = models.CharField(
        verbose_name="Is a follow-up to this report required?",
        max_length=15,
        choices=YES_NO,
        default=YES,
        help_text="If NO, this will be considered the final report",
    )

    class Meta:
        abstract = True
