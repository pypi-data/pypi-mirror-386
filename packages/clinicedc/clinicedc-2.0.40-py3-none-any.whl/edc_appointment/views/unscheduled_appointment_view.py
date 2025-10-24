from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.http.response import HttpResponseRedirect
from django.urls.base import reverse
from django.utils.html import format_html
from django.views.generic.base import View

from ..creators import UnscheduledAppointmentCreator
from ..exceptions import (
    AppointmentInProgressError,
    AppointmentPermissionsRequired,
    AppointmentWindowError,
    CreateAppointmentError,
    InvalidParentAppointmentMissingVisitError,
    InvalidParentAppointmentStatusError,
    UnscheduledAppointmentError,
    UnscheduledAppointmentNotAllowed,
)


class UnscheduledAppointmentView(View):
    """A view that creates an unscheduled appointment and redirects to
    the subject dashboard.

    Source Url is usually reversed in the Appointment model wrapper.
    Redirect url name comes in kwargs.
    """

    unscheduled_appointment_cls = UnscheduledAppointmentCreator
    dashboard_template_name = "subject_dashboard_template"

    def get(self, request, *args, **kwargs):  # noqa: ARG002
        kwargs["suggested_visit_code_sequence"] = int(kwargs["visit_code_sequence"])
        kw = dict(
            subject_identifier=kwargs.get("subject_identifier"),
            visit_schedule_name=kwargs.get("visit_schedule_name"),
            schedule_name=kwargs.get("schedule_name"),
            visit_code=kwargs.get("visit_code"),
            suggested_visit_code_sequence=kwargs.get("suggested_visit_code_sequence"),
            suggested_appt_datetime=kwargs.get("appt_datetime"),
            facility=kwargs.get("facility"),
            request=request,
        )

        try:
            creator = self.unscheduled_appointment_cls(**kw)
        except (
            CreateAppointmentError,
            ObjectDoesNotExist,
            UnscheduledAppointmentError,
            InvalidParentAppointmentMissingVisitError,
            InvalidParentAppointmentStatusError,
            AppointmentInProgressError,
            AppointmentWindowError,
            AppointmentPermissionsRequired,
            UnscheduledAppointmentNotAllowed,
        ) as e:
            messages.error(self.request, str(e))
        else:
            messages.success(
                self.request,
                format_html(
                    "Appointment {appt} was created successfully.",
                    appt=creator.appointment,  # nosec B308, B703
                ),
            )
            messages.warning(
                self.request,
                format_html(
                    "Remember to adjust the appointment date and time on appointment {appt}.",
                    appt=creator.appointment,  # nosec B308, B703
                ),
            )
        return HttpResponseRedirect(
            reverse(
                self.kwargs.get("redirect_url"),
                kwargs={"subject_identifier": kwargs.get("subject_identifier")},
            )
        )
