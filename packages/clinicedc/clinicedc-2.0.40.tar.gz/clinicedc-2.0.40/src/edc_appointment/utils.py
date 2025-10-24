from __future__ import annotations

import calendar
import sys
import warnings
from collections.abc import Callable
from datetime import datetime
from typing import TYPE_CHECKING, Any

from dateutil.relativedelta import relativedelta
from django.apps import apps as django_apps
from django.conf import settings
from django.contrib import messages
from django.contrib.admin.utils import NotRelationField, get_model_from_relation
from django.contrib.messages import ERROR, SUCCESS
from django.core.exceptions import (
    ImproperlyConfigured,
    ObjectDoesNotExist,
    ValidationError,
)
from django.core.handlers.wsgi import WSGIRequest
from django.db import transaction
from django.db.models import Count, ProtectedError
from django.urls import reverse
from django.utils.translation import gettext as _
from edc_constants.constants import CLINIC, NOT_APPLICABLE, OK
from edc_constants.constants import ERROR as ERROR_CODE
from edc_dashboard.url_names import url_names
from edc_form_validators import INVALID_ERROR
from edc_metadata.constants import CRF, REQUIRED, REQUISITION
from edc_metadata.utils import (
    get_crf_metadata_model_cls,
    get_requisition_metadata_model_cls,
    has_keyed_metadata,
)
from edc_utils.date import to_local
from edc_utils.text import convert_php_dateformat
from edc_visit_schedule.exceptions import (
    ScheduledVisitWindowError,
    UnScheduledVisitWindowError,
)
from edc_visit_schedule.site_visit_schedules import site_visit_schedules
from edc_visit_schedule.utils import get_default_max_visit_window_gap, is_baseline
from edc_visit_tracking.utils import get_allow_missed_unscheduled_appts

from .choices import DEFAULT_APPT_REASON_CHOICES
from .constants import (
    CANCELLED_APPT,
    COMPLETE_APPT,
    INCOMPLETE_APPT,
    MISSED_APPT,
    NEW_APPT,
    SCHEDULED_APPT,
    SKIPPED_APPT,
    UNSCHEDULED_APPT,
)
from .exceptions import (
    AppointmentBaselineError,
    AppointmentDatetimeError,
    AppointmentMissingValuesError,
    AppointmentWindowError,
    UnscheduledAppointmentError,
)

if TYPE_CHECKING:
    from decimal import Decimal

    from django.db.models import QuerySet
    from edc_crf.model_mixins import CrfModelMixin as Base
    from edc_metadata.model_mixins.creates import CreatesMetadataModelMixin

    from .models import Appointment, AppointmentType

    class RelatedVisitModel(CreatesMetadataModelMixin, Base):
        appointment: Appointment


class AppointmentDateWindowPeriodGapError(Exception):
    pass


class AppointmentAlreadyStarted(Exception):  # noqa: N818
    pass


def get_appointment_model_name() -> str:
    return "edc_appointment.appointment"


def get_appointment_model_cls() -> type[Appointment]:
    return django_apps.get_model(get_appointment_model_name())


def get_appointment_type_model_name() -> str:
    return "edc_appointment.appointmenttype"


def get_appointment_type_model_cls() -> type[AppointmentType]:
    return django_apps.get_model(get_appointment_type_model_name())


def get_allow_skipped_appt_using() -> dict[str, tuple[str, str]]:
    """Return dict from settings or empty dictionary.

    For example:
         = {"my_app.crfone": ("next_appt_date", "next_visit_code")}
    """
    dct = getattr(settings, "EDC_APPOINTMENT_ALLOW_SKIPPED_APPT_USING", {})
    if len(dct.keys()) > 1:
        raise ImproperlyConfigured(
            "Only one model may be specified. See "
            f"settings.EDC_APPOINTMENT_ALLOW_SKIPPED_APPT_USING. Got {dct}."
        )
    return dct


def get_max_months_to_next_appointment():
    return getattr(settings, "EDC_APPOINTMENT_MAX_MONTHS_TO_NEXT_APPT", 6)


def allow_clinic_on_weekend():
    return getattr(settings, "EDC_APPOINTMENT_ALLOW_CLINIC_ON_WEEKENDS", False)


def get_max_months_to_next_appointment_as_rdelta():
    max_months = get_max_months_to_next_appointment()
    return relativedelta(months=max_months)


def raise_on_appt_may_not_be_missed(
    appointment: Appointment = None,
    appt_timing: str | None = None,
):
    if appointment.id:
        appt_timing = appt_timing or appointment.appt_timing
        if (
            appt_timing
            and appt_timing in [MISSED_APPT, NOT_APPLICABLE]
            and is_baseline(instance=appointment)
        ):
            errmsg = "Invalid. A baseline appointment may not be reported as missed"
            if appt_timing == NOT_APPLICABLE:
                errmsg = "This field is applicable"
            raise AppointmentBaselineError(errmsg)
        if (
            appointment.visit_code_sequence is not None
            and appt_timing
            and appointment.visit_code_sequence > 0
            and appt_timing == MISSED_APPT
            and not get_allow_missed_unscheduled_appts()
        ):
            raise UnscheduledAppointmentError(
                "Invalid. An unscheduled appointment may not be reported as missed."
                "Try to cancel the appointment instead. "
            )


def get_appointment_form_meta_options() -> dict:
    return getattr(
        settings, "EDC_APPOINTMENT_FORM_META_OPTIONS", dict(labels={}, help_texts={})
    )


def get_appt_reason_choices() -> tuple[str, ...]:
    """Returns a customized tuple of choices otherwise the default.

    Note: You can only change the right side of any tuple.

    For example:
      ((SCHEDULED_APPT, "some custom text"),
        (UNSCHEDULED_APPT, "some custom text"))

    See also: formfield_for_choice_field in modeladmin class.
    """

    settings_attr = "EDC_APPOINTMENT_APPT_REASON_CHOICES"
    appt_reason_choices = getattr(settings, settings_attr, DEFAULT_APPT_REASON_CHOICES)
    keys = sorted([choice[0] for choice in appt_reason_choices])
    if SCHEDULED_APPT not in keys or UNSCHEDULED_APPT not in keys:
        raise ImproperlyConfigured(
            "Invalid value for EDC_APPOINTMENT_APPT_REASON_CHOICES. "
            f"Expected a choices tuple with keys `{SCHEDULED_APPT}` and `{UNSCHEDULED_APPT}`. "
            f"See {settings_attr}."
        )
    return appt_reason_choices


def get_appt_type_default() -> str:
    """Returns the default appointment type name."""
    return getattr(settings, "EDC_APPOINTMENT_APPT_TYPE_DEFAULT", CLINIC)


def get_appt_reason_default() -> str:
    """Returns the default appointment reason."""
    value = getattr(settings, "EDC_APPOINTMENT_APPT_REASON_DEFAULT", None)
    if not value:
        value = getattr(settings, "EDC_APPOINTMENT_DEFAULT_APPT_REASON", None)
        warnings.warn(
            "Settings attribute `EDC_APPOINTMENT_DEFAULT_APPT_REASON` has "
            "been deprecated in favor of `EDC_APPOINTMENT_APPT_REASON_DEFAULT`. ",
            DeprecationWarning,
            stacklevel=2,
        )
    return value or SCHEDULED_APPT


def cancelled_appointment(appointment: Appointment) -> None:
    """Try to delete subject visit if appt status = CANCELLED_APPT"""
    try:
        cancelled = appointment.appt_status == CANCELLED_APPT
    except AttributeError as e:
        if "appt_status" not in str(e):
            raise
    else:
        if (
            cancelled
            and appointment.visit_code_sequence > 0
            and "historical" not in appointment._meta.label_lower
            and not appointment.crf_metadata_keyed_exists
            and not appointment.requisition_metadata_keyed_exists
        ):
            try:
                related_visit = appointment.related_visit_model_cls().objects.get(
                    appointment=appointment
                )
            except ObjectDoesNotExist:
                appointment.delete()
            else:
                with transaction.atomic():
                    try:
                        related_visit.delete()
                    except ProtectedError:
                        pass
                    else:
                        appointment.delete()


def missed_appointment(appointment: Appointment) -> None:
    """Try to create_missed_visit_from_appointment if
    appt_status == missed.
    """
    try:
        missed = appointment.appt_timing == MISSED_APPT
    except AttributeError as e:
        if "appt_timing" not in str(e):
            raise
    else:
        if (
            missed
            and appointment.visit_code_sequence == 0
            and "historical" not in appointment._meta.label_lower
        ):
            try:
                appointment.create_missed_visit_from_appointment()
            except AttributeError as e:
                if "create_missed_visit" not in str(e):
                    raise


def reset_visit_code_sequence_or_pass(
    subject_identifier: str,
    visit_schedule_name: str,
    schedule_name: str,
    visit_code: str,
    appointment: Appointment | None = None,
    write_stdout: bool | None = None,
) -> Appointment | None:
    """Validate the order of the appointment visit code sequences
    relative to the appt_datetime and reset the visit code sequences
    if needed.

    Delete and recreate metadata

    Also do the same for the `related_visit`, if it exists.
    """
    opts = dict(
        subject_identifier=subject_identifier,
        visit_schedule_name=visit_schedule_name,
        schedule_name=schedule_name,
        visit_code=visit_code,
    )
    qs = get_appointment_model_cls().objects.filter(**opts).order_by("appt_datetime")
    expected = list(range(0, qs.count()))
    actual = [o.visit_code_sequence for o in qs]
    if actual != expected:
        if write_stdout:
            sys.stdout.write(
                "     - Resetting for "
                f"{subject_identifier} {visit_code}: {actual=} {expected=} ...\n"
            )
        # reset visit code sequence for this visit code
        get_crf_metadata_model_cls().objects.filter(visit_code_sequence__gt=0, **opts).delete()
        get_requisition_metadata_model_cls().objects.filter(
            visit_code_sequence__gt=0, **opts
        ).delete()

        with transaction.atomic():
            # set appt and related visit visit_code_sequences to the
            # negative of the current value
            for obj in get_appointment_model_cls().objects.filter(
                visit_code_sequence__gt=0, **opts
            ):
                obj.visit_code_sequence = obj.visit_code_sequence * -1
                obj.save_base(update_fields=["visit_code_sequence"])
                if getattr(obj, "related_visit", None):
                    obj.related_visit.visit_code_sequence = obj.visit_code_sequence
                    obj.related_visit.save_base(update_fields=["visit_code_sequence"])
                    obj.related_visit.metadata_create()

            # reset sequence order by appt_datetime
            for index, obj in enumerate(
                get_appointment_model_cls()
                .objects.filter(visit_code_sequence__lt=0, **opts)
                .order_by("appt_datetime"),
                start=1,
            ):
                obj.visit_code_sequence = index
                obj.save_base(update_fields=["visit_code_sequence"])
                if getattr(obj, "related_visit", None):
                    obj.related_visit.visit_code_sequence = index
                    obj.related_visit.save_base(update_fields=["visit_code_sequence"])
                    obj.related_visit.metadata_create()

        if appointment:
            # refresh the given appt if not None since
            # appointment visit_code_sequence may have changed
            appointment = get_appointment_model_cls().objects.get(id=appointment.id)
    return appointment


def reset_visit_code_sequence_for_subject(
    subject_identifier: str,
    visit_schedule_name: str,
    schedule_name: str,
) -> None:
    """Resets / validates appointment `visit code sequences` for any
    `visit code` with unscheduled appointments for the given subject
     and schedule.

     Wrapper for function `reset_visit_code_sequence_or_pass`.
    """
    ann = (
        get_appointment_model_cls()
        .objects.values("visit_code")
        .filter(subject_identifier=subject_identifier, visit_code_sequence__gt=0)
        .annotate(Count("visit_code"))
    )
    for visit_code in [obj.get("visit_code") for obj in ann]:
        reset_visit_code_sequence_or_pass(
            subject_identifier=subject_identifier,
            visit_schedule_name=visit_schedule_name,
            schedule_name=schedule_name,
            visit_code=visit_code,
        )


def delete_appointment_in_sequence(appointment: Any, from_post_delete=None) -> None:
    if not from_post_delete:
        with transaction.atomic():
            appointment.delete()
        reset_visit_code_sequence_or_pass(
            subject_identifier=appointment.subject_identifier,
            visit_schedule_name=appointment.visit_schedule_name,
            schedule_name=appointment.schedule_name,
            visit_code=appointment.visit_code,
        )


def update_appt_status(appointment: Appointment, save: bool | None = None):
    """Sets appt_status, and if save is True, calls save_base().

    This is useful if checking `appt_status` is correct
    relative to the visit tracking model and CRFs and
    requisitions
    """
    if appointment.appt_status in (CANCELLED_APPT, SKIPPED_APPT):
        pass
    elif not appointment.related_visit:
        appointment.appt_status = NEW_APPT
    elif (
        appointment.crf_metadata_required_exists
        or appointment.requisition_metadata_required_exists
    ):
        appointment.appt_status = INCOMPLETE_APPT
    else:
        appointment.appt_status = COMPLETE_APPT
    if save:
        appointment.save_base(update_fields=["appt_status"])
        appointment.refresh_from_db()
    return appointment


def get_previous_appointment(
    appointment: Appointment, include_interim: bool | None = None
) -> Appointment | None:
    """Returns the previous appointment model instance,
    or None, in this schedule.

    Keywords:
        * include_interim: include interim appointments
          (e.g. those where visit_code_sequence != 0)

    See also: `AppointmentMethodsModelMixin`
    """
    check_appointment_required_values_or_raise(appointment)
    opts: dict[str, str | int | Decimal] = dict(
        subject_identifier=appointment.subject_identifier,
        visit_schedule_name=appointment.visit_schedule_name,
        schedule_name=appointment.schedule_name,
    )
    if include_interim:
        if appointment.visit_code_sequence != 0:
            opts.update(
                visit_code_sequence__lt=appointment.visit_code_sequence,
                timepoint__lte=appointment.timepoint,
            )
        else:
            opts.update(timepoint__lt=appointment.timepoint)
    elif not include_interim:
        opts.update(
            visit_code_sequence=0,
            timepoint__lt=appointment.timepoint,
        )

    appointments: QuerySet[Appointment] = (
        appointment.__class__.objects.filter(**opts)
        .exclude(id=appointment.id)
        .order_by("timepoint", "visit_code_sequence")
    )

    try:
        previous_appt = appointments.reverse()[0]
    except IndexError:
        previous_appt = None
    return previous_appt


def get_next_appointment(appointment: Appointment, include_interim=None) -> Appointment | None:
    """Returns the next appointment model instance,
    or None, in this schedule.

    Keywords:
        * include_interim: include interim appointments
          (e.g. those where visit_code_sequence != 0)

    See also: `AppointmentMethodsModelMixin`
    """
    next_appt: Appointment | None = None
    check_appointment_required_values_or_raise(appointment)
    opts: dict[str, str | int | Decimal] = dict(
        subject_identifier=appointment.subject_identifier,
        visit_schedule_name=appointment.visit_schedule_name,
        schedule_name=appointment.schedule_name,
    )
    if include_interim:
        break_on_next = False
        for obj in appointment.__class__.objects.filter(
            timepoint__gte=appointment.timepoint, **opts
        ).order_by("timepoint", "visit_code_sequence"):
            if break_on_next:
                next_appt = obj
                break
            if obj.id == appointment.id:
                break_on_next = True
    elif not include_interim:
        opts.update(
            timepoint__gt=appointment.timepoint,
            visit_code_sequence=0,
        )
        next_appt = (
            appointment.__class__.objects.filter(**opts)
            .exclude(id=appointment.id)
            .order_by("timepoint", "visit_code_sequence")
        ).first()
    return next_appt


def check_appointment_required_values_or_raise(appointment: Appointment) -> None:
    if (
        not appointment.visit_schedule_name
        or not appointment.schedule_name
        or not appointment.visit_code
        or appointment.visit_code_sequence is None
        or appointment.timepoint is None
    ):
        raise AppointmentMissingValuesError(
            f"Appointment instance is missing required values. See {appointment}."
        )


def raise_on_appt_datetime_not_in_window(
    appointment: Appointment,
    appt_datetime: datetime | None = None,
    baseline_timepoint_datetime: datetime | None = None,
) -> None:
    if appointment.appt_status != CANCELLED_APPT and not is_baseline(instance=appointment):
        baseline_timepoint_datetime = baseline_timepoint_datetime or (
            appointment.__class__.objects.first_appointment(
                subject_identifier=appointment.subject_identifier,
                visit_schedule_name=appointment.visit_schedule_name,
                schedule_name=appointment.schedule_name,
            ).timepoint_datetime
        )
        try:
            appointment.schedule.datetime_in_window(
                dt=appt_datetime or appointment.appt_datetime,
                timepoint_datetime=appointment.timepoint_datetime,
                visit_code=appointment.visit_code,
                visit_code_sequence=appointment.visit_code_sequence,
                baseline_timepoint_datetime=baseline_timepoint_datetime,
            )
        except ScheduledVisitWindowError as e:
            msg = str(e)
            msg.replace("Invalid datetime", "Invalid appointment datetime (S)")
            raise AppointmentWindowError(msg) from e
        except UnScheduledVisitWindowError as e:
            msg = str(e)
            msg.replace("Invalid datetime", "Invalid appointment datetime (U)")
            raise AppointmentWindowError(msg) from e


def get_window_gap_days(appointment) -> int:
    """Return the number of days betwen this visit's upper and the
    next visit's lower.

    See get_default_max_visit_window_gap and settings attr.
    """
    if not appointment.next:
        gap_days = 0
    else:
        gap_days = abs(
            (appointment.timepoint_datetime + appointment.visit.rupper)
            - (appointment.next.timepoint_datetime - appointment.next.visit.rlower)
        ).days
    return gap_days


def appt_datetime_in_gap(appointment: Appointment, suggested_appt_datetime: datetime) -> bool:
    """Return True if datetime falls in a gap between this and the
    next appointment window.
    """
    in_gap = False
    if get_window_gap_days(appointment) > 0:
        next_lower_datetime = (
            appointment.next.timepoint_datetime - appointment.next.visit.rlower
        )
        upper_datetime = appointment.timepoint_datetime + appointment.visit.rupper
        if upper_datetime < suggested_appt_datetime < next_lower_datetime:
            in_gap = True
    return in_gap


def get_max_window_gap_to_lower(appointment) -> int:
    if (
        appointment.visit.max_window_gap_to_lower is not None
        and appointment.visit.max_window_gap_to_lower < get_default_max_visit_window_gap()
    ):
        max_gap = appointment.visit.max_window_gap_to_lower
    else:
        max_gap = get_default_max_visit_window_gap()
    return max_gap


def appt_datetime_in_next_window_adjusted_for_gap(
    appointment: Appointment, suggested_appt_datetime: datetime
) -> bool:
    """Returns True if `suggest_datetime` falls between the
    NEXT appointment's lower and upper window period datetime after
    adding gap_days to the lower datetime.
    """
    in_window = False
    gap_days = get_window_gap_days(appointment)
    max_gap = get_max_window_gap_to_lower(appointment)
    gap_days = min(gap_days, max_gap)
    if gap_days > 0:
        next_lower_datetime = (
            appointment.next.timepoint_datetime
            - appointment.next.visit.rlower
            - relativedelta(days=gap_days)
        )
        next_upper_datetime = (
            appointment.next.timepoint_datetime + appointment.next.visit.rupper
        )
        if next_lower_datetime <= suggested_appt_datetime <= next_upper_datetime:
            in_window = True
    return in_window


def get_appointment_by_datetime(
    suggested_appt_datetime: datetime,
    subject_identifier: str,
    visit_schedule_name: str,
    schedule_name: str,
    raise_if_in_gap: bool | None = None,
) -> Appointment | None:
    """Returns an appointment where the suggested datetime falls
    within the window period.

    * Returns None if no appointment is found.
    * Raises an exception if there is a gap between upper and lower
      boundaries and the date falls within the gap.
    """
    appointment = None
    raise_if_in_gap = True if raise_if_in_gap is None else raise_if_in_gap
    appointments = (
        django_apps.get_model("edc_appointment.appointment")
        .objects.filter(
            subject_identifier=subject_identifier,
            visit_schedule_name=visit_schedule_name,
            schedule_name=schedule_name,
            visit_code_sequence=0,
        )
        .order_by("timepoint_datetime")
    )
    for appointment in appointments:
        if appointment.appt_status == CANCELLED_APPT or is_baseline(appointment):
            continue
        try:
            raise_on_appt_datetime_not_in_window(
                appointment, appt_datetime=suggested_appt_datetime
            )
        except AppointmentWindowError as e:
            in_gap = appt_datetime_in_gap(appointment, suggested_appt_datetime)
            in_next_window_adjusted = appt_datetime_in_next_window_adjusted_for_gap(
                appointment, suggested_appt_datetime
            )
            if in_gap and raise_if_in_gap:
                dt = suggested_appt_datetime.strftime(
                    convert_php_dateformat(settings.SHORT_DATE_FORMAT)
                )
                raise AppointmentDateWindowPeriodGapError(
                    f"Date falls in a `window period gap` between {appointment.visit_code} "
                    f"and {appointment.next.visit_code}. Got {dt}."
                ) from e
            if (
                in_gap
                and in_next_window_adjusted
                and appointment.next.visit.add_window_gap_to_lower
            ):
                appointment = appointment.next  # noqa: PLW2901
                break
            if (
                in_gap
                and not in_next_window_adjusted
                and appointment.next.visit.add_window_gap_to_lower
            ):
                appointment = None  # noqa: PLW2901
                break
            appointment = appointment.next  # noqa: PLW2901
        else:
            break
    return appointment


def reset_appointment(appointment: Appointment, **kwargs):
    """Reset appointment but only if appointment has not started.

    Will overwrite the default field values with values
    from kwargs.

    If field in kwargs refers to a field class with a related_model
    and the value is not found, the field will be set to None without
    raising an ObjectDoesNotExist exception.
    """
    if has_keyed_metadata(appointment) or appointment.related_visit:
        raise AppointmentAlreadyStarted(
            f"Unable to reset. Appointment already started. Got {appointment}."
        )
    defaults = dict(
        appt_status=appointment._meta.get_field("appt_status").default,
        appt_timing=appointment._meta.get_field("appt_timing").default,
        appt_type=None,
        appt_type_other="",
        appt_datetime=appointment.timepoint_datetime,
        comment="",
    )
    defaults.update(**kwargs)
    for k, v in defaults.items():
        try:
            related_model = get_model_from_relation(appointment._meta.get_field(k))
        except NotRelationField:
            setattr(appointment, k, v)
        else:
            try:
                setattr(appointment, k, related_model.objects.get(name=v))
            except ObjectDoesNotExist:
                setattr(appointment, k, None)
    appointment.save_base(update_fields=[*defaults.keys()])


def skip_appointment(appointment: Appointment, comment: str | None = None):
    """Set appointment to `SKIPPED_APPT` if appointment has not
    started.
    """
    if has_keyed_metadata(appointment) or appointment.related_visit:
        raise AppointmentAlreadyStarted(
            f"Unable to skip. Appointment already started. Got {appointment}."
        )
    reset_appointment(
        appointment,
        appt_status=SKIPPED_APPT,
        appt_timing=NOT_APPLICABLE,
        appt_type=NOT_APPLICABLE,
        comment=comment or "",
    )


def get_unscheduled_appointment_url(appointment: Appointment = None) -> str:
    """Returns a url for the unscheduled appointment."""
    dashboard_url = url_names.get("subject_dashboard_url")
    unscheduled_appointment_url = "edc_appointment:unscheduled_appointment_url"
    kwargs = dict(
        subject_identifier=appointment.subject_identifier,
        visit_schedule_name=appointment.visit_schedule_name,
        schedule_name=appointment.schedule_name,
        visit_code=appointment.visit_code,
        visit_code_sequence=appointment.visit_code_sequence + 1,
        timepoint=appointment.timepoint,
    )
    kwargs.update(visit_code_sequence=str(appointment.visit_code_sequence + 1))
    kwargs.update(redirect_url=dashboard_url)
    return reverse(unscheduled_appointment_url, kwargs=kwargs)


def update_appt_status_for_timepoint(related_visit: RelatedVisitModel) -> None:
    """Only check COMPLETE_APPT and INCOMPLETE_APPT against metadata."""
    if related_visit.appointment.appt_status == COMPLETE_APPT:
        if (
            related_visit.metadata[CRF].filter(entry_status=REQUIRED).exists()
            or related_visit.metadata[REQUISITION].filter(entry_status=REQUIRED).exists()
        ):
            related_visit.appointment.appt_status = INCOMPLETE_APPT
            related_visit.appointment.save_base(update_fields=["appt_status"])
    elif related_visit.appointment.appt_status == INCOMPLETE_APPT and (
        not related_visit.metadata[CRF].filter(entry_status=REQUIRED).exists()
        and not related_visit.metadata[REQUISITION].filter(entry_status=REQUIRED).exists()
    ):
        related_visit.appointment.appt_status = COMPLETE_APPT
        related_visit.appointment.save_base(update_fields=["appt_status"])


def refresh_appointments(
    subject_identifier: str,
    visit_schedule_name: str,
    schedule_name: str,
    request: WSGIRequest | None = None,
    warn_only: bool | None = None,
) -> tuple[str, str]:
    status = OK
    visit_schedule = site_visit_schedules.get_visit_schedule(visit_schedule_name)
    schedule = visit_schedule.schedules.get(schedule_name)
    try:
        schedule.refresh_schedule(subject_identifier)
    except AppointmentDatetimeError as e:
        if request and not warn_only:
            status = ERROR_CODE
            messages.add_message(
                request=request,
                level=ERROR,
                message=_(
                    "An error was encountered when refreshing appointments. "
                    "Contact your administrator. Got '%(error_msg)s'."
                )
                % dict(error_msg=str(e)),
            )
        elif warn_only:
            warnings.warn(str(e), stacklevel=2)
        else:
            raise
    else:
        for appointment in get_appointment_model_cls().objects.filter(
            subject_identifier=subject_identifier,
            visit_schedule_name=visit_schedule_name,
            schedule_name=schedule_name,
        ):
            if appointment.related_visit:
                update_appt_status_for_timepoint(appointment.related_visit)
    if status == OK and request:
        messages.add_message(
            request,
            SUCCESS,
            _("The appointments for %(subject_identifier)s have been refreshed")
            % dict(subject_identifier=subject_identifier),
        )
    return subject_identifier, status


def validate_date_is_on_clinic_day(
    cleaned_data: dict, clinic_days: list[int], raise_validation_error: Callable | None = None
):
    raise_validation_error = raise_validation_error or ValidationError
    if cleaned_data.get("appt_date"):
        try:
            appt_date = to_local(cleaned_data.get("appt_date")).date()
        except AttributeError:
            appt_date = cleaned_data.get("appt_date")
        try:
            report_date = to_local(cleaned_data.get("report_datetime")).date()
        except AttributeError:
            report_date = cleaned_data.get("report_datetime")
        day_abbr = calendar.weekheader(3).split(" ")
        if appt_date == report_date:
            raise raise_validation_error(
                {"appt_date": "Cannot be equal to the report datetime"}, INVALID_ERROR
            )
        if appt_date <= report_date:
            raise raise_validation_error(
                {"appt_date": "Cannot be before the report datetime"}, INVALID_ERROR
            )
        if not allow_clinic_on_weekend() and calendar.weekday(
            appt_date.year, appt_date.month, appt_date.day
        ) in [calendar.SATURDAY, calendar.SUNDAY]:
            raise raise_validation_error(
                {
                    "appt_date": _("Expected %(mon)s-%(fri)s. Got %(day)s")
                    % {
                        "mon": day_abbr[calendar.MONDAY],
                        "fri": day_abbr[calendar.FRIDAY],
                        "day": day_abbr[
                            calendar.weekday(appt_date.year, appt_date.month, appt_date.day)
                        ],
                    }
                },
                INVALID_ERROR,
            )
        if (
            clinic_days
            and calendar.weekday(appt_date.year, appt_date.month, appt_date.day)
            not in clinic_days
        ):
            days_str = [day_abbr[d] for d in clinic_days]
            raise raise_validation_error(
                {
                    "appt_date": _(
                        "Invalid clinic day. Expected %(expected)s. Got %(day_abbr)s"
                    )
                    % {
                        "expected": ", ".join(days_str),
                        "day_abbr": appt_date.strftime("%A"),
                    }
                },
                INVALID_ERROR,
            )
