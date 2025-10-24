from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from dateutil.relativedelta import relativedelta
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist

from edc_utils import formatted_date, formatted_datetime, to_local
from edc_visit_schedule.site_visit_schedules import site_visit_schedules
from edc_visit_schedule.utils import get_lower_datetime

from ..constants import (
    COMPLETE_APPT,
    IN_PROGRESS_APPT,
    INCOMPLETE_APPT,
    NEW_APPT,
    UNSCHEDULED_APPT,
)
from ..exceptions import (
    AppointmentInProgressError,
    AppointmentPermissionsRequired,
    AppointmentWindowError,
    CreateAppointmentError,
    InvalidParentAppointmentMissingVisitError,
    InvalidParentAppointmentStatusError,
    InvalidVisitCodeSequencesError,
    UnscheduledAppointmentError,
    UnscheduledAppointmentNotAllowed,
)
from .appointment_creator import AppointmentCreator

if TYPE_CHECKING:
    from edc_facility import Facility
    from edc_visit_schedule.visit import Visit

    from ..models import Appointment

__all__ = ["UnscheduledAppointmentCreator"]


class UnscheduledAppointmentCreator:
    """Attempts to create a new unscheduled appointment where the
    visit code sequence == the given `visit_code_sequence` or raises.
    """

    appointment_creator_cls = AppointmentCreator

    def __init__(
        self,
        *,
        subject_identifier: str,
        visit_schedule_name: str,
        schedule_name: str,
        visit_code: str,
        suggested_visit_code_sequence: int | None = None,
        suggested_appt_datetime: datetime | None = None,
        facility: Facility | None = None,
        request: Any | None = None,
    ):
        self._parent_appointment = None
        self._calling_appointment = None
        self._suggested_appt_datetime = None

        self.appointment = None

        self.subject_identifier = subject_identifier
        self.visit_schedule_name = visit_schedule_name
        self.schedule_name = schedule_name

        self.visit_code = visit_code
        self.visit_code_sequence = suggested_visit_code_sequence
        if self.visit_code_sequence is None:
            raise InvalidVisitCodeSequencesError("visit code sequence cannot be None")
        if self.visit_code_sequence < 1:
            raise InvalidVisitCodeSequencesError(
                "suggested visit code sequence cannot be less than 1"
            )
        self.facility = facility
        self.visit_schedule = site_visit_schedules.get_visit_schedule(visit_schedule_name)
        self.schedule = self.visit_schedule.schedules.get(schedule_name)
        self.appointment_model_cls = self.schedule.appointment_model_cls
        self.visit = self.visit_schedule.schedules.get(self.schedule_name).visits.get(
            self.visit_code
        )
        self.suggested_appt_datetime = suggested_appt_datetime
        self.has_perm_or_raise(request)
        self.create_or_raise()

    @property
    def visit(self) -> Visit:
        return self._visit

    @visit.setter
    def visit(self, value: Visit | None):
        if not value:
            raise UnscheduledAppointmentError(
                "Invalid visit. Got None using {"
                f"visit_schedule_name='{self.visit_schedule_name}',"
                f"schedule_name='{self.schedule_name}',"
                f"visit_code='{self.visit_code}'" + "}"
            )
        if not value.allow_unscheduled:
            raise UnscheduledAppointmentNotAllowed(
                f"Not allowed. Visit {self.visit_code} is not configured for "
                "unscheduled appointments."
            )
        self._visit = value

    def create_or_raise(self) -> None:
        """Create the unscheduled appointment.

        Do not allow new unscheduled if any appointments are IN_PROGRESS

        Note: `timepoint` and `timepoint_datetime` are not incremented
            for unscheduled appointments. These values are carried
            over from the parent appointment values.

        """
        try:
            obj = self.appointment_model_cls.objects.get(
                subject_identifier=self.subject_identifier,
                visit_schedule_name=self.visit_schedule_name,
                schedule_name=self.schedule_name,
                appt_status=IN_PROGRESS_APPT,
            )
        except MultipleObjectsReturned as e:
            raise UnscheduledAppointmentError(e) from e
        except ObjectDoesNotExist:
            pass
        else:
            raise AppointmentInProgressError(
                f"Not allowed. Appointment {obj.visit_code}."
                f"{obj.visit_code_sequence} is in progress."
            )
        try:
            appointment_creator = self.appointment_creator_cls(
                subject_identifier=self.subject_identifier,
                visit_schedule_name=self.visit_schedule_name,
                schedule_name=self.schedule_name,
                visit=self.visit,
                suggested_datetime=self.suggested_appt_datetime,
                timepoint=self.parent_appointment.timepoint,
                timepoint_datetime=self.parent_appointment.timepoint_datetime,
                visit_code_sequence=self.parent_appointment.next_visit_code_sequence,
                facility=self.facility,
                appt_status=NEW_APPT,
                appt_reason=UNSCHEDULED_APPT,
                ignore_window_period=self.ignore_window_period,
            )
        except CreateAppointmentError:
            raise
        except AppointmentWindowError as e:
            msg = str(e).replace("Perhaps catch this in the form", "")
            raise UnscheduledAppointmentError(
                f"Unable to create unscheduled appointment. {msg}"
            ) from e
        self.appointment = appointment_creator.appointment

    def has_perm_or_raise(self, request) -> None:
        if request and not request.user.has_perm(
            f"{self.appointment_model_cls._meta.app_label}."
            f"add_{self.appointment_model_cls._meta.model_name}"
        ):
            raise AppointmentPermissionsRequired(
                "You do not have permission to create an appointment"
            )

    @property
    def suggested_appt_datetime(self):
        return self._suggested_appt_datetime

    def after_calling_appt_or_raise(self, suggested_dte: datetime):
        """Raises if on same day or before otherwise returns True"""
        suggested_dt = to_local(suggested_dte).date()
        calling_dt = to_local(self.calling_appointment.appt_datetime).date()
        if suggested_dt <= calling_dt:
            suggested = formatted_date(suggested_dt)
            calling = formatted_date(calling_dt)
            raise CreateAppointmentError(
                "Suggested appointment date must be after the calling appointment date. "
                f"Got {suggested} not after {calling}."
            )
        return True

    @suggested_appt_datetime.setter
    def suggested_appt_datetime(self, suggested_dte: datetime | None):
        if suggested_dte and self.after_calling_appt_or_raise(suggested_dte):
            self._suggested_appt_datetime = suggested_dte
        else:
            self._suggested_appt_datetime = (
                self.calling_appointment.appt_datetime + relativedelta(days=1)
            )
        if self.parent_appointment.next and self.suggested_appt_datetime >= get_lower_datetime(
            self.parent_appointment.next
        ):
            dt = formatted_datetime(self.suggested_appt_datetime)
            next_dt = formatted_datetime(get_lower_datetime(self.parent_appointment.next))
            raise UnscheduledAppointmentError(
                "Appointment date exceeds window period. Next appointment is "
                f"{self.parent_appointment.next.visit_code} and lower window starts "
                f"on {next_dt}. Got {dt}. Perhaps catch this in the form."
            )

    @property
    def calling_appointment(self) -> Appointment:
        """Returns the appointment which precedes the to-be-created
        unscheduled appt.

        It must exist.

        Note: subtracting 1 from `visit_code_sequence` implies the
        visit_code_sequence cannot be less than 1.

        if visit_code_sequence = 1, calling_appointment and parent_appointment
        will be the same instance.
        """
        if not self._calling_appointment:
            opts = dict(
                subject_identifier=self.subject_identifier,
                visit_schedule_name=self.visit_schedule_name,
                schedule_name=self.schedule_name,
                visit_code=self.visit_code,
                visit_code_sequence=self.visit_code_sequence - 1,
                timepoint=self.parent_appointment.timepoint,
            )
            self._calling_appointment = self.appointment_model_cls.objects.get(**opts)
        return self._calling_appointment

    @property
    def parent_appointment(self) -> Appointment:
        """Returns the parent or 'scheduled' appointment
        (visit_code_sequence=0).
        """
        if not self._parent_appointment:
            options = dict(
                subject_identifier=self.subject_identifier,
                visit_schedule_name=self.visit_schedule_name,
                schedule_name=self.schedule_name,
                visit_code=self.visit_code,
                visit_code_sequence=0,
            )
            self._parent_appointment = self.appointment_model_cls.objects.get(**options)
            if not self._parent_appointment.related_visit:
                raise InvalidParentAppointmentMissingVisitError(
                    "Unable to create unscheduled appointment. An unscheduled "
                    "appointment cannot be created if the parent appointment's "
                    "visit form is not submitted. "
                    f"Got appointment '{self.visit_code}.0'."
                )
            if self._parent_appointment.appt_status not in [
                COMPLETE_APPT,
                INCOMPLETE_APPT,
            ]:
                raise InvalidParentAppointmentStatusError(
                    "Unable to create unscheduled appointment. An unscheduled "
                    "appointment cannot be created if the parent appointment "
                    "is 'new' or 'in progress'. Got appointment "
                    f"'{self.visit_code}' is "
                    f"{self._parent_appointment.get_appt_status_display().lower()}."
                )

        return self._parent_appointment

    @property
    def ignore_window_period(self: Any) -> bool:
        value = False
        if (
            self.calling_appointment
            and self.calling_appointment.next
            and self.calling_appointment.next.appt_status in [INCOMPLETE_APPT, COMPLETE_APPT]
            and self.suggested_appt_datetime < self.calling_appointment.next.appt_datetime
        ):
            value = True
        return value
