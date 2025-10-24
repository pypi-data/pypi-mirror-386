from django.db import models

from edc_model_fields.fields import OtherCharField

from ..choices import APPT_STATUS, APPT_TIMING, DEFAULT_APPT_REASON_CHOICES
from ..constants import NEW_APPT, ONTIME_APPT


class AppointmentFieldsModelMixin(models.Model):
    timepoint = models.DecimalField(
        null=True, decimal_places=1, max_digits=6, help_text="timepoint from schedule"
    )

    timepoint_datetime = models.DateTimeField(
        null=True, help_text="Unadjusted datetime calculated from visit schedule"
    )

    appt_close_datetime = models.DateTimeField(
        null=True,
        help_text=(
            "timepoint_datetime adjusted according to the nearest "
            "available datetime for this facility"
        ),
    )

    facility_name = models.CharField(
        max_length=25,
        help_text="set by model that creates appointments, e.g. Enrollment",
    )

    appt_datetime = models.DateTimeField(
        verbose_name="Appointment date and time", db_index=True
    )

    appt_type = models.ForeignKey(
        "edc_appointment.AppointmentType",
        verbose_name="Appointment type",
        on_delete=models.PROTECT,
        null=True,
        blank=False,
        help_text="",
    )

    appt_type_other = OtherCharField(
        verbose_name="If other appointment type, please specify ...",
    )

    appt_status = models.CharField(
        verbose_name="Status",
        choices=APPT_STATUS,
        max_length=25,
        default=NEW_APPT,
        db_index=True,
        help_text=(
            "If the visit has already begun, only 'in progress', "
            "'incomplete' or 'done' are valid options. Only unscheduled appointments "
            "may be cancelled."
        ),
    )

    appt_reason = models.CharField(
        verbose_name="Reason for appointment",
        max_length=25,
        choices=DEFAULT_APPT_REASON_CHOICES,
        help_text=(
            "The reason for visit from the visit report will be validated against "
            "this response. Refer to the protocol documentation for the definition "
            "of a scheduled appointment."
        ),
    )

    appt_timing = models.CharField(
        verbose_name="Timing",
        max_length=25,
        choices=APPT_TIMING,
        default=ONTIME_APPT,
        help_text=(
            "If late, you may also be required to complete a protocol incident report. "
            "Refer to the protocol documentation for the allowed window periods "
            "of scheduled appointments."
        ),
    )

    comment = models.CharField("Comment", max_length=250, blank=True, default="")

    is_confirmed = models.BooleanField(default=False, editable=False)

    ignore_window_period = models.BooleanField(default=False, editable=False)

    class Meta:
        abstract = True
