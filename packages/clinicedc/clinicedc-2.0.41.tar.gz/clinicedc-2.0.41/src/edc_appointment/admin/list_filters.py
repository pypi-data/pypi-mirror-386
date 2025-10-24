from __future__ import annotations

from dateutil.relativedelta import relativedelta
from django.contrib.admin import SimpleListFilter
from django.db.models import QuerySet
from django.utils import timezone
from django.utils.translation import gettext as _

from edc_appointment.choices import APPT_STATUS
from edc_appointment.constants import (
    ATTENDED_APPT,
    COMPLETE_APPT,
    GTE_30_TO_60_DAYS,
    GTE_60_TO_90_DAYS,
    GTE_90_TO_180_DAYS,
    GTE_180,
    IN_PROGRESS_APPT,
    INCOMPLETE_APPT,
    LT_30_DAYS,
)
from edc_model_admin.list_filters import FutureDateListFilter


class AppointmentListFilter(FutureDateListFilter):
    title = _("Appointment date")

    parameter_name = "appt_datetime"
    field_name = "appt_datetime"


class AppointmentStatusListFilter(SimpleListFilter):
    title = _("Status")

    parameter_name = "appt_status"
    field_name = "appt_status"

    def lookups(self, request, model_admin) -> tuple[tuple[str, str], ...]:  # noqa: ARG002
        return *APPT_STATUS, (ATTENDED_APPT, "Attended (In progress, incomplete, done)")

    def queryset(self, request, queryset):  # noqa: ARG002
        qs = None
        if self.value() == ATTENDED_APPT:
            qs = queryset.filter(
                appt_status__in=[IN_PROGRESS_APPT, INCOMPLETE_APPT, COMPLETE_APPT]
            )
        elif self.value():
            qs = queryset.filter(appt_status=self.value())
        return qs


class AppointmentOverdueListFilter(SimpleListFilter):
    title = "Overdue (days)"
    parameter_name = "overdue"

    def lookups(self, request, model_admin) -> tuple[tuple[str, str], ...]:  # noqa: ARG002
        return (
            (LT_30_DAYS, _("2-30 days")),
            (GTE_30_TO_60_DAYS, _("30-60 days")),
            (GTE_60_TO_90_DAYS, _("60-90 days")),
            (GTE_90_TO_180_DAYS, _("90-180 days")),
            (GTE_180, _("180+ days")),
        )

    def queryset(self, request, queryset) -> QuerySet | None:  # noqa: ARG002
        now = timezone.now().replace(second=59, hour=23, minute=59)
        qs = None
        if self.value() == LT_30_DAYS:
            qs = queryset.filter(
                appt_datetime__gt=now - relativedelta(days=30),
                appt_datetime__lte=now - relativedelta(days=2),
            ).order_by("appt_datetime")
        elif self.value() == GTE_30_TO_60_DAYS:
            qs = queryset.filter(
                appt_datetime__gt=now - relativedelta(days=60),
                appt_datetime__lte=now - relativedelta(days=30),
            ).order_by("appt_datetime")
        elif self.value() == GTE_60_TO_90_DAYS:
            qs = queryset.filter(
                appt_datetime__gt=now - relativedelta(days=90),
                appt_datetime__lte=now - relativedelta(days=60),
            ).order_by("appt_datetime")
        elif self.value() == GTE_90_TO_180_DAYS:
            qs = queryset.filter(
                appt_datetime__gt=now - relativedelta(days=180),
                appt_datetime__lte=now - relativedelta(days=90),
            ).order_by("appt_datetime")
        elif self.value() == GTE_180:
            qs = queryset.filter(
                appt_datetime__lte=now - relativedelta(days=180),
            ).order_by("appt_datetime")
        return qs
