from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING, Any

from django.apps import apps as django_apps
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext as _

from edc_sites.site import sites

from ..constants import (
    CANCELLED_APPT,
    COMPLETE_APPT,
    IN_PROGRESS_APPT,
    INCOMPLETE_APPT,
    NEW_APPT,
    SKIPPED_APPT,
)

if TYPE_CHECKING:
    from django.db.models import QuerySet

    from ..models import Appointment


class AppointmentViewMixin:
    """A view mixin to handle appointments on the dashboard."""

    def __init__(self, **kwargs):
        self._appointment = None
        self._appointments = None
        self.appointment_model: str = "edc_appointment.appointment"
        self.appointment_id: str | None = None
        super().__init__(**kwargs)

    def get(self, request, *args, **kwargs):
        self.appointment_id = kwargs.get("appointment")
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        if self.appointment:
            if self.appointment.appt_status != IN_PROGRESS_APPT:
                message = _(
                    'You have selected an appointment that is no longer "in progress". '
                    "Refer to the schedule for the appointment that is "
                    'currently "in progress".'
                )
                self.message_user(message, level=messages.WARNING)
            if self.appointment.related_visit:
                report_datetime = self.appointment.related_visit.report_datetime
                kwargs.update(report_datetime=report_datetime)
        has_call_manager = bool(django_apps.app_configs.get("edc_call_manager"))
        kwargs.update(
            appointment=self.appointment,
            appointments=self.appointments,
            CANCELLED_APPT=CANCELLED_APPT,
            COMPLETE_APPT=COMPLETE_APPT,
            INCOMPLETE_APPT=INCOMPLETE_APPT,
            IN_PROGRESS_APPT=IN_PROGRESS_APPT,
            NEW_APPT=NEW_APPT,
            SKIPPED_APPT=SKIPPED_APPT,
            has_call_manager=has_call_manager,
        )
        return super().get_context_data(**kwargs)

    @property
    def appointment_model_cls(self) -> Appointment:
        return django_apps.get_model(self.appointment_model)

    @property
    def appointment_options(self) -> dict[str, Any]:
        opts = {}
        if self.kwargs.get("appointment"):
            opts = dict(id=self.kwargs.get("appointment"))
        elif (
            self.kwargs.get("subject_identifier")
            and self.kwargs.get("visit_schedule_name")
            and self.kwargs.get("schedule_name")
            and self.kwargs.get("visit_code")
        ):
            visit_code_sequence = self.kwargs.get("visit_code_sequence") or 0
            opts = dict(
                subject_identifier=self.kwargs.get("subject_identifier"),
                visit_schedule_name=self.kwargs.get("visit_schedule_name"),
                schedule_name=self.kwargs.get("schedule_name"),
                visit_code=self.kwargs.get("visit_code"),
                visit_code_sequence=visit_code_sequence,
                site_id__in=sites.get_site_ids_for_user(request=self.request),
            )
        return opts

    @property
    def appointment(self) -> Appointment:
        if not self._appointment and self.appointment_id:
            try:
                self._appointment = self.appointment_model_cls.objects.get(
                    id=self.appointment_id
                )
            except ObjectDoesNotExist:
                if opts := self.appointment_options:
                    with contextlib.suppress(ObjectDoesNotExist):
                        self._appointment = self.appointment_model_cls.objects.get(**opts)
        return self._appointment

    @property
    def appointments(self) -> QuerySet[Appointment]:
        """Returns a Queryset of all appointments for this subject."""
        if not self._appointments:
            self._appointments = self.appointment_model_cls.objects.filter(
                subject_identifier=self.subject_identifier,
                site_id__in=sites.get_site_ids_for_user(request=self.request),
            ).order_by("timepoint", "visit_code_sequence")

        return self._appointments
