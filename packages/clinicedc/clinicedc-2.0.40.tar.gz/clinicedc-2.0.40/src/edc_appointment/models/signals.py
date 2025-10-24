from django.core.exceptions import ObjectDoesNotExist
from django.db.models.signals import post_delete, post_save, pre_delete
from django.dispatch import receiver
from django.utils import timezone

from edc_constants.constants import NO
from edc_utils.text import formatted_datetime
from edc_visit_schedule.site_visit_schedules import site_visit_schedules
from edc_visit_tracking.utils import get_related_visit_model_cls

from ..appointment_status_updater import (
    AppointmentStatusUpdater,
    AppointmentStatusUpdaterError,
)
from ..constants import IN_PROGRESS_APPT, NEW_APPT
from ..creators import create_next_appointment_as_interim
from ..managers import AppointmentDeleteError
from ..model_mixins import NextAppointmentCrfModelMixin
from ..skip_appointments import SkipAppointments
from ..utils import (
    cancelled_appointment,
    get_allow_skipped_appt_using,
    get_appointment_model_name,
    missed_appointment,
    reset_visit_code_sequence_or_pass,
)
from .appointment import Appointment


@receiver(post_save, sender=Appointment, weak=False, dispatch_uid="appointment_post_save")
def appointment_post_save(sender, instance, raw, update_fields, **kwargs):
    if not raw and not update_fields:
        # use the AppointmentStatusUpdater to set all
        # other appointments to be NOT in progress
        try:
            if instance.appt_status == IN_PROGRESS_APPT:
                AppointmentStatusUpdater(
                    instance,
                    change_to_in_progress=True,
                    clear_others_in_progress=True,
                )
        except AttributeError as e:
            if "appt_status" not in str(e):
                raise
        except AppointmentStatusUpdaterError:
            pass
    # don't indent!
    # try to create_missed_visit_from_appointment
    #  if appt_status == missed
    missed_appointment(instance)
    # try to delete subject visit
    # if appt status = CANCELLED_APPT
    cancelled_appointment(instance)


@receiver(post_save, weak=False, dispatch_uid="create_appointments_on_post_save")
def create_appointments_on_post_save(sender, instance, raw, created, using, **kwargs):
    """Method `Model.create_appointments` is not typically used.

    See schedule.put_on_schedule() in edc_visit_schedule.
    """
    if not raw and not kwargs.get("update_fields"):
        try:
            instance.create_appointments()
        except AttributeError as e:
            if "create_appointments" not in str(e):
                raise


@receiver(post_save, weak=False, dispatch_uid="update_appt_status_on_related_visit_post_save")
def update_appt_status_on_related_visit_post_save(
    sender, instance, created, raw, update_fields, **kwargs
):
    if (
        not raw
        and not update_fields
        and created
        and isinstance(instance, (get_related_visit_model_cls(),))
    ):
        try:
            AppointmentStatusUpdater(
                instance.appointment,
                change_to_in_progress=True,
                clear_others_in_progress=True,
            )
        except AttributeError as e:
            if "appointment" not in str(e):
                raise
        except AppointmentStatusUpdaterError:
            pass


@receiver(
    post_delete,
    weak=False,
    dispatch_uid="update_appt_status_on_related_visit_post_delete",
)
def update_appt_status_on_related_visit_post_delete(sender, instance, using, **kwargs):
    if isinstance(instance, (get_related_visit_model_cls(),)):
        try:
            appointment = instance.appointment
        except AttributeError as e:
            if "appointment" not in str(e):
                raise
        else:
            appointment.appt_status = NEW_APPT
            appointment.save_base(update_fields=["appt_status"])


@receiver(
    pre_delete,
    sender=Appointment,
    weak=False,
    dispatch_uid="appointments_on_pre_delete",
)
def appointments_on_pre_delete(sender, instance, using, **kwargs):
    if instance.visit_code_sequence == 0:
        schedule = site_visit_schedules.get_visit_schedule(
            instance.visit_schedule_name
        ).schedules.get(instance.schedule_name)
        onschedule_datetime = schedule.onschedule_model_cls.objects.get(
            subject_identifier=instance.subject_identifier
        ).onschedule_datetime
        # get visits for this consent/consent ext
        visits = schedule.visits_for_subject(
            subject_identifier=instance.subject_identifier,
            report_datetime=onschedule_datetime,
            site_id=instance.site_id,
        )
        if instance.visit_code in [visit for visit in visits]:
            try:
                offschedule_datetime = schedule.offschedule_model_cls.objects.get(
                    subject_identifier=instance.subject_identifier
                ).offschedule_datetime
            except ObjectDoesNotExist as e:
                raise AppointmentDeleteError(
                    f"Appointment may not be deleted. "
                    f"Subject {instance.subject_identifier} is on schedule "
                    f"'{instance.visit_schedule.verbose_name}.{instance.schedule_name}' "
                    f"as of '{formatted_datetime(onschedule_datetime)}'. "
                    f"Got appointment {instance.visit_code}.{instance.visit_code_sequence} "
                    f"datetime {formatted_datetime(instance.appt_datetime)}. "
                    f"Perhaps complete off schedule model "
                    f"'{instance.schedule.offschedule_model_cls().verbose_name.title()}' "
                    f"first."
                ) from e
            else:
                if onschedule_datetime <= instance.appt_datetime <= offschedule_datetime:
                    raise AppointmentDeleteError(
                        f"Appointment may not be deleted. "
                        f"Subject {instance.subject_identifier} is on schedule "
                        f"'{instance.visit_schedule.verbose_name}.{instance.schedule_name}' "
                        f"as of '{formatted_datetime(onschedule_datetime)}' "
                        f"until '{formatted_datetime(timezone.now())}'. "
                        f"Got appointment datetime "
                        f"{formatted_datetime(instance.appt_datetime)}. "
                    )


@receiver(
    post_delete,
    sender=Appointment,
    weak=False,
    dispatch_uid="appointments_on_post_delete",
)
def appointments_on_post_delete(sender, instance, using, **kwargs):
    if (
        not kwargs.get("update_fields")
        and sender._meta.label_lower == get_appointment_model_name()
    ):
        reset_visit_code_sequence_or_pass(
            subject_identifier=instance.subject_identifier,
            visit_schedule_name=instance.visit_schedule_name,
            schedule_name=instance.schedule_name,
            visit_code=instance.visit_code,
        )


@receiver(
    post_save,
    weak=False,
    dispatch_uid="update_appointments_to_next_on_post_save",
)
def update_appointments_to_next_on_post_save(sender, instance, raw, created, using, **kwargs):
    if (
        not raw
        and not kwargs.get("update_fields")
        and get_allow_skipped_appt_using().get(instance._meta.label_lower)
    ):
        skip_appt = SkipAppointments(instance)
        next_appointment_updated = skip_appt.update()
        allow_create_interim = getattr(instance, "allow_create_interim", False)
        if not next_appointment_updated and allow_create_interim:
            create_next_appointment_as_interim(
                next_appt_datetime=skip_appt.next_appt_datetime,
                appointment=skip_appt.appointment,
            )


@receiver(post_delete, weak=False, dispatch_uid="update_appointments_to_next_on_post_delete")
def update_appointments_to_next_on_post_delete(sender, instance, using, **kwargs):
    if get_allow_skipped_appt_using().get(instance._meta.label_lower):
        SkipAppointments(instance).reset_appointments()


@receiver(
    post_save,
    weak=False,
    dispatch_uid="update_appointment_from_nextappointment_post_save",
)
def update_appointment_from_nextappointment_post_save(
    sender, instance, raw, created, using, **kwargs
):
    if (
        not raw
        and not kwargs.get("update_fields")
        and isinstance(instance, (NextAppointmentCrfModelMixin,))
        and instance.offschedule_today == NO
    ):
        appointment = Appointment.objects.get(pk=instance.related_visit.appointment.next.id)
        appointment.appt_datetime = instance.appt_datetime
        appointment.save()
