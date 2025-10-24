from edc_action_item.managers import (
    ActionIdentifierModelManager,
    ActionIdentifierSiteManager,
)
from edc_action_item.models import ActionModelMixin
from edc_identifier.model_mixins import NonUniqueSubjectIdentifierFieldMixin
from edc_model.models import BaseUuidModel
from edc_sites.model_mixins import SiteModelMixin

from ..constants import PROTOCOL_DEVIATION_VIOLATION_ACTION
from ..model_mixins import ProtocolDeviationViolationModelMixin


class ProtocolDeviationViolation(
    ProtocolDeviationViolationModelMixin,
    NonUniqueSubjectIdentifierFieldMixin,
    SiteModelMixin,
    ActionModelMixin,
    BaseUuidModel,
):
    action_name = PROTOCOL_DEVIATION_VIOLATION_ACTION
    on_site = ActionIdentifierSiteManager()
    objects = ActionIdentifierModelManager()

    def natural_key(self):
        return (self.action_identifier,)

    class Meta(ProtocolDeviationViolationModelMixin.Meta, BaseUuidModel.Meta):
        indexes = (
            *ProtocolDeviationViolationModelMixin.Meta.indexes,
            *NonUniqueSubjectIdentifierFieldMixin.Meta.indexes,
            *ActionModelMixin.Meta.indexes,
            *BaseUuidModel.Meta.indexes,
        )
