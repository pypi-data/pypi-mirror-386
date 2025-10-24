class SubjectScheduleError(Exception):
    pass


class NotOnScheduleError(Exception):
    pass


class OnScheduleError(Exception):
    pass


class OffScheduleError(Exception):
    pass


class NotOffScheduleError(Exception):
    pass


class NotOnScheduleForDateError(Exception):
    pass


class OnScheduleForDateError(Exception):
    pass


class OnScheduleFirstAppointmentDateError(Exception):
    pass


class UnknownSubjectError(Exception):
    pass


class InvalidOffscheduleDate(Exception):  # noqa: N818
    pass


class ScheduleError(Exception):
    pass


class ScheduledVisitWindowError(Exception):
    pass


class UnScheduledVisitError(Exception):
    pass


class UnScheduledVisitWindowError(Exception):
    pass


class MissedVisitError(Exception):
    pass


class SiteVisitScheduleError(Exception):
    pass


class RegistryNotLoaded(Exception):  # noqa: N818
    pass


class AlreadyRegisteredVisitSchedule(Exception):  # noqa: N818
    pass


class VisitScheduleBaselineError(Exception):
    pass


class VisitScheduleNonCrfModelFormMixinError(Exception):
    pass
