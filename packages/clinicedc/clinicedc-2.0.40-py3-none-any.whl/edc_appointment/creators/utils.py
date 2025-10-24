from __future__ import annotations

import contextlib
from datetime import datetime
from typing import TYPE_CHECKING

from dateutil.relativedelta import relativedelta
from django.db import transaction

from ..constants import INCOMPLETE_APPT, NEW_APPT
from .unscheduled_appointment_creator import (
    CreateAppointmentError,
    UnscheduledAppointmentCreator,
)

if TYPE_CHECKING:
    from ..models import Appointment


def create_next_appointment_as_interim(
    appointment: Appointment, next_appt_datetime: datetime | None = None
) -> Appointment | None:
    return create_unscheduled_appointment(appointment, next_appt_datetime=next_appt_datetime)


def create_unscheduled_appointment(
    appointment: Appointment,
    next_appt_datetime: datetime | None = None,
) -> Appointment | None:
    """Create and return an unscheduled appointment if
    `next_appt_datetime` is within the window period of
    `appointment`.

    """
    unscheduled_appointment = None
    next_appt_datetime = next_appt_datetime or appointment.appt_datetime + relativedelta(
        days=1
    )
    # next_appointment = get_appointment_by_datetime(
    #     next_appt_datetime,
    #     appointment.subject_identifier,
    #     appointment.visit_schedule_name,
    #     appointment.schedule_name,
    #     raise_if_in_gap=False,
    # )
    # if appointment == next_appointment:
    if (
        appointment.relative_next
        and appointment.relative_next.appt_status == NEW_APPT
        and appointment.relative_next.visit_code_sequence > 0
    ):
        appointment.relative_next.delete()
    appt_status = appointment.appt_status
    appointment.appt_status = INCOMPLETE_APPT
    appointment.save_base(update_fields=["appt_status"])
    with transaction.atomic(), contextlib.suppress(CreateAppointmentError):
        unscheduled_appointment = UnscheduledAppointmentCreator(
            subject_identifier=appointment.subject_identifier,
            visit_schedule_name=appointment.visit_schedule_name,
            schedule_name=appointment.schedule_name,
            visit_code=appointment.visit_code,
            facility=appointment.facility,
            suggested_appt_datetime=next_appt_datetime,
            suggested_visit_code_sequence=appointment.visit_code_sequence + 1,
        )
    appointment.appt_status = appt_status
    appointment.save_base(update_fields=["appt_status"])
    return getattr(unscheduled_appointment, "appointment", None)
