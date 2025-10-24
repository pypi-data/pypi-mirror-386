from django.db import models

from edc_action_item.managers import (
    ActionIdentifierModelManager,
    ActionIdentifierSiteManager,
)
from edc_action_item.models import ActionModelMixin
from edc_identifier.model_mixins import NonUniqueSubjectIdentifierFieldMixin
from edc_pdf_reports.model_mixins import PdfReportModelMixin
from edc_sites.model_mixins import SiteModelMixin

from ...constants import AE_INITIAL_ACTION
from ...pdf_reports import AePdfReport
from .ae_initial_ae_model_mixin import AeInitialAeModelMixin
from .ae_initial_fields_model_mixin import AeInitialFieldsModelMixin
from .ae_initial_methods_model_mixin import AeInitialMethodsModelMixin
from .ae_initial_sae_model_mixin import AeInitialSaeModelMixin
from .ae_initial_susar_model_mixin import AeInitialSusarModelMixin
from .ae_initial_tmg_model_mixin import AeInitialTmgModelMixin


class AeInitialModelMixin(
    SiteModelMixin,
    ActionModelMixin,
    NonUniqueSubjectIdentifierFieldMixin,
    AeInitialFieldsModelMixin,
    AeInitialMethodsModelMixin,
    AeInitialAeModelMixin,
    AeInitialSaeModelMixin,
    AeInitialSusarModelMixin,
    AeInitialTmgModelMixin,
    PdfReportModelMixin,
    models.Model,
):
    action_name = AE_INITIAL_ACTION

    pdf_report_cls = AePdfReport

    objects = ActionIdentifierModelManager()

    on_site = ActionIdentifierSiteManager()

    class Meta(NonUniqueSubjectIdentifierFieldMixin.Meta):
        abstract = True
        verbose_name = "AE Initial Report"
        indexes = (
            *NonUniqueSubjectIdentifierFieldMixin.Meta.indexes,
            *ActionModelMixin.Meta.indexes,
            models.Index(fields=["subject_identifier", "action_identifier", "site"]),
        )
