from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING
from uuid import UUID

from .model_button import ModelButton

if TYPE_CHECKING:
    from django.contrib.sites.models import Site

    from edc_appointment.models import Appointment
    from edc_crf.model_mixins import CrfModelMixin
    from edc_lab.model_mixins import RequisitionModelMixin
    from edc_metadata.models import CrfMetadata, RequisitionMetadata
    from edc_model.models import BaseUuidModel

    class CrfModel(CrfModelMixin, BaseUuidModel): ...

    class RequisitionModel(RequisitionModelMixin, BaseUuidModel): ...


__all__ = ["DashboardModelButton"]


@dataclass
class DashboardModelButton(ModelButton):
    """
    Base class for buttons that appear on the subject dashboard.

    Note:
        dashboard_url_name: key in global `url_names`
        See edc_dashboard.

    """

    model_obj: CrfModel | RequisitionModel | None = None
    metadata_model_obj: CrfMetadata | RequisitionMetadata | None = None
    appointment: Appointment | None = None
    next_url_name: str = field(default="subject_dashboard_url")
    model_cls: type[CrfModel | RequisitionModel] = field(default=None, init=False)

    def __post_init__(self):
        self.model_cls = self.metadata_model_obj.model_cls
        self.model_obj = self.metadata_model_obj.model_instance

    @property
    def site(self) -> Site | None:
        """If model_obj is None, then Site should come from the
        CRFMetadata or RequisitionMetadata models.
        """
        return getattr(self.model_obj, "site", None) or getattr(
            self.metadata_model_obj, "site", None
        )

    @property
    def reverse_kwargs(self) -> dict[str, str | UUID]:
        return dict(
            subject_identifier=self.appointment.subject_identifier,
            appointment=self.appointment.id,
        )
