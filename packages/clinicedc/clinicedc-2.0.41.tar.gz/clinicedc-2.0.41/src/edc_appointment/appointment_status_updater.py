from __future__ import annotations

from typing import TYPE_CHECKING

from .constants import IN_PROGRESS_APPT
from .utils import update_appt_status

if TYPE_CHECKING:
    from .models import Appointment


class AppointmentStatusUpdaterError(Exception):
    pass


class AppointmentStatusUpdater:
    def __init__(
        self,
        appointment: Appointment,
        change_to_in_progress: bool | None = None,
        clear_others_in_progress: bool | None = None,
    ):
        self.appointment = appointment
        if "historical" in self.appointment._meta.label_lower:
            raise AppointmentStatusUpdaterError(
                f"Not an Appointment model instance. Got {self.appointment._meta.label_lower}."
            )
        if not getattr(self.appointment, "id", None):
            raise AppointmentStatusUpdaterError(
                "Appointment instance must exist. Got `id` is None"
            )
        if change_to_in_progress and self.appointment.appt_status != IN_PROGRESS_APPT:
            self.appointment.appt_status = IN_PROGRESS_APPT
            self.appointment.save_base(update_fields=["appt_status"])
        if clear_others_in_progress:
            for appt in self.appointment.__class__.objects.filter(
                visit_schedule_name=self.appointment.visit_schedule_name,
                schedule_name=self.appointment.schedule_name,
                appt_status=IN_PROGRESS_APPT,
            ).exclude(id=self.appointment.id):
                update_appt_status(appt, save=True)
