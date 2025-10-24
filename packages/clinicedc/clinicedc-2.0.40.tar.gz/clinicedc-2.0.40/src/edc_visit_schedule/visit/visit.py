from __future__ import annotations

import re
from decimal import Decimal
from typing import TYPE_CHECKING

from django.apps import apps as django_apps
from django.utils import timezone

from edc_facility.utils import get_default_facility_name, get_facility
from edc_utils.date import to_local

from .crf import Crf
from .crf_collection import CrfCollection
from .forms_collection import FormsCollection
from .requisition_collection import RequisitionCollection
from .window_period import WindowPeriod

if TYPE_CHECKING:
    from datetime import datetime

    from dateutil.relativedelta import relativedelta

    from edc_facility.facility import Facility

    from .requisition import Requisition


class VisitCodeError(Exception):
    pass


class VisitDateError(Exception):
    pass


class VisitError(Exception):
    pass


class BaseDatetimeNotSet(Exception):  # noqa: N818
    pass


def base_datetime_required():
    raise BaseDatetimeNotSet(
        "Base datetime is None, set the base datetime before accessing attr"
    )


class VisitDate:
    window_period_cls = WindowPeriod

    def __init__(
        self,
        *,
        rlower: relativedelta,
        rupper: relativedelta,
        timepoint: Decimal | None = None,
        base_timepoint: Decimal | None = None,
    ):
        self._base: datetime | None = None
        self._lower: datetime | None = None
        self._upper: datetime | None = None
        self._window_period = self.window_period_cls(
            rlower=rlower,
            rupper=rupper,
            timepoint=timepoint,
            base_timepoint=base_timepoint,
        )

    @property
    def base(self) -> datetime:
        return self._base

    @base.setter
    def base(self, dt: datetime):
        self._base = to_local(dt)
        self._lower, self._upper = self._window_period.get_window(dt=self._base)

    @property
    def lower(self) -> datetime:
        if not self.base:
            raise BaseDatetimeNotSet(
                "Base datetime is None, set the base datetime before accessing attr lower"
            )
        return self._lower

    @property
    def upper(self) -> datetime:
        if not self.base:
            raise BaseDatetimeNotSet(
                "Base datetime is None, set the base datetime before accessing attr upper"
            )
        return self._upper


class Visit:
    code_regex = r"^([A-Z0-9])+$"
    visit_date_cls = VisitDate

    def __init__(
        self,
        code: str,
        timepoint: int | float | Decimal,
        rbase: relativedelta,
        rlower: relativedelta,
        rupper: relativedelta,
        title: str | None = None,
        facility_name: str | None = None,
        crfs: CrfCollection | None = None,
        crfs_prn: CrfCollection | None = None,
        crfs_unscheduled: CrfCollection | None = None,
        crfs_missed: CrfCollection | None = None,
        requisitions: RequisitionCollection | None = None,
        requisitions_prn: RequisitionCollection | None = None,
        requisitions_unscheduled: RequisitionCollection | None = None,
        rlower_late: relativedelta = None,
        rupper_late: relativedelta = None,
        add_window_gap_to_lower: bool | None = None,
        max_window_gap_to_lower: int | None = None,
        allow_unscheduled: bool | None = None,
        instructions: str | None = None,
        base_timepoint: int | float | Decimal | None = None,
        grouping=None,
    ):
        self.next = None
        if isinstance(base_timepoint, (float,)):
            base_timepoint = Decimal(str(base_timepoint))
        elif isinstance(base_timepoint, (int,)):
            base_timepoint = Decimal(str(base_timepoint) + ".0")
        self.base_timepoint = base_timepoint or Decimal("0.0")
        self.crfs: CrfCollection = crfs or CrfCollection()
        self.crfs_unscheduled: CrfCollection = crfs_unscheduled or CrfCollection()
        self.crfs_missed: CrfCollection = crfs_missed or CrfCollection(
            Crf(show_order=1, model="edc_visit_tracking.subjectvisitmissed", required=True)
        )
        self.crfs_prn: CrfCollection = crfs_prn or CrfCollection()
        for prn in self.crfs_prn:
            prn.required = False
        self.requisitions: RequisitionCollection = requisitions or RequisitionCollection()
        self.requisitions_unscheduled: RequisitionCollection = (
            requisitions_unscheduled or RequisitionCollection()
        )
        self.requisitions_prn: RequisitionCollection = (
            requisitions_prn or RequisitionCollection()
        )
        for prn in self.requisitions_prn:
            prn.required = False
        self.instructions = instructions
        if isinstance(timepoint, (float,)):
            timepoint = Decimal(str(timepoint))
        elif isinstance(timepoint, (int,)):
            timepoint = Decimal(str(timepoint) + ".0")
        self.timepoint = timepoint
        self.rbase = rbase
        self.rlower = rlower
        self.rupper = rupper
        self.rlower_late = self.rlower if rlower_late is None else rlower_late
        self.rupper_late = self.rupper if rupper_late is None else rupper_late
        self.add_window_gap_to_lower = add_window_gap_to_lower
        self.max_window_gap_to_lower = max_window_gap_to_lower
        self.grouping = grouping
        if not code or isinstance(code, int) or not re.match(self.code_regex, code):
            raise VisitCodeError(f"Invalid visit code. Got '{code}'")
        self.code = code  # unique
        self.dates = self.visit_date_cls(
            rlower=self.rlower,
            rupper=self.rupper,
            timepoint=self.timepoint,
            base_timepoint=self.base_timepoint,
        )
        self.late_dates = self.visit_date_cls(
            rlower=self.rlower_late,
            rupper=self.rupper_late,
            timepoint=self.timepoint,
            base_timepoint=self.base_timepoint,
        )
        utcnow = timezone.now()
        self.validate_rlower_late(utcnow)
        self.validate_rupper_late(utcnow)
        self.title = title or f"Visit {self.code}"
        self.name = self.code
        self.facility_name = facility_name or get_default_facility_name()
        self.allow_unscheduled = allow_unscheduled
        if self.allow_unscheduled and not crfs_unscheduled:
            raise VisitError(
                f"crfs_unscheduled may not be null if allow_unscheduled=True. See {self!r}"
            )
        if timepoint is None:
            raise VisitError(f"Timepoint not specified. Got None. See Visit {code}.")

    def __repr__(self):
        return f"{self.__class__.__name__}({self.code}, {self.timepoint})"

    def __str__(self):
        return self.title

    @property
    def scheduled_forms(self) -> FormsCollection:
        """Returns a FormsCollection of scheduled forms."""
        return FormsCollection(*self.crfs, *self.requisitions, name="scheduled_forms")

    @property
    def unscheduled_forms(self) -> FormsCollection:
        """Returns a FormsCollection of unscheduled forms."""
        return FormsCollection(
            *self.crfs_unscheduled,
            *self.requisitions_unscheduled,
            name="unscheduled_forms",
        )

    @property
    def prn_forms(self) -> FormsCollection:
        """Returns a FormsCollection of prn forms."""
        return FormsCollection(*self.crfs_prn, *self.requisitions_prn, name="prn_forms")

    @property
    def all_crfs(self) -> CrfCollection:
        """Return a new collection containing all crfs.

        The new collection contains:
             * crfs
             * crfs_unscheduled
             * crfs_prn
             * crfs_missed
        """
        crfs = list(self.crfs) + [
            crf
            for crf in self.crfs_unscheduled
            if crf.model not in [crf.model for crf in self.crfs]
        ]
        crfs = crfs + [
            crf for crf in self.crfs_missed if crf.model not in [crf.model for crf in crfs]
        ]
        crfs = crfs + [
            crf for crf in self.crfs_prn if crf.model not in [crf.model for crf in crfs]
        ]
        return CrfCollection(*crfs, name="all_crfs", check_sequence=False)

    @property
    def all_requisitions(self) -> RequisitionCollection:
        """Return a new collection containing all requisitions.

        The new collection contains:
             * requisitions
             * requisitions_unscheduled
             * requisitions_prn
        """
        names = [r.name for r in self.requisitions]
        requisitions = list(self.requisitions) + [
            r for r in self.requisitions_unscheduled if r.name not in names
        ]
        names = list(set([r.name for r in requisitions]))
        requisitions = requisitions + [r for r in self.requisitions_prn if r.name not in names]
        return RequisitionCollection(
            *requisitions, name="all_requisitions", check_sequence=False
        )

    def get_crf(self, model=None) -> Crf | None:
        get_crf = None
        for crf in self.crfs:
            if crf.model == model:
                get_crf = crf
                break
        return get_crf

    def get_requisition(self, model=None, panel_name=None) -> Requisition | None:
        get_requisition = None
        for requisition in self.requisitions:
            if requisition.model == model and requisition.panel.name == panel_name:
                get_requisition = requisition
                break
        return get_requisition

    def get_models(self) -> list:
        models = [django_apps.get_model(crf.model) for crf in self.crfs]
        models.extend(
            [django_apps.get_model(requisition.model) for requisition in self.requisitions]
        )
        return models

    @property
    def facility(self) -> Facility | None:
        """Returns a Facility object."""
        if self.facility_name:
            return get_facility(name=self.facility_name)
        return None

    @property
    def timepoint_datetime(self) -> datetime:
        return self.dates.base

    @timepoint_datetime.setter
    def timepoint_datetime(self, dt=None):
        self.dates.base = to_local(dt)

    def to_dict(self):
        return dict(
            crfs=[(crf.model, crf.required) for crf in self.crfs],
            crfs_unscheduled=[(crf.model, crf.required) for crf in self.crfs_unscheduled],
            crfs_prn=[(crf.model, crf.required) for crf in self.crfs_prn],
            crfs_missed=[(crf.model, crf.required) for crf in self.crfs_missed],
            requisitions=[
                (requisition.panel.name, requisition.required)
                for requisition in self.requisitions
            ],
            requisitions_unscheduled=[
                (requisition.panel.name, requisition.required)
                for requisition in self.requisitions_unscheduled
            ],
            requisitions_prn=[
                (requisition.model, requisition.required)
                for requisition in self.requisitions_prn
            ],
        )

    def validate_rlower_late(self, utcnow):
        if utcnow - self.rlower_late < utcnow - self.rlower:
            raise VisitDateError(
                "Lower bound error. `Late` lower boundary cannot exceed "
                f"lower boundary. See {self}."
            )

    def validate_rupper_late(self, utcnow):
        if utcnow + self.rupper_late < utcnow + self.rupper:
            raise VisitDateError(
                "Upper bound error. `Late` upper boundary cannot be exceed "
                f"upper boundary. See {self}."
            )
