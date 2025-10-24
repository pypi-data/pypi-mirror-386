from __future__ import annotations

from collections import namedtuple
from typing import TYPE_CHECKING, Any

from django.core.exceptions import ValidationError

from edc_visit_schedule.visit import RequisitionCollection

from ...requisition import RequisitionMetadataUpdater
from ..rule_group import RuleGroup
from ..rule_group_meta_options import RuleGroupMetaOptions
from ..rule_group_metaclass import RuleGroupMetaclass

RuleResult = namedtuple("RuleResult", "target_panel entry_status")

if TYPE_CHECKING:
    from edc_visit_tracking.model_mixins import VisitModelMixin as Base

    from ...model_mixins.creates import CreatesMetadataModelMixin
    from ...models import RequisitionMetadata

    class RelatedVisitModel(CreatesMetadataModelMixin, Base):
        pass


class RequisitionRuleGroupMetaOptionsError(ValidationError):
    pass


class RequisitionRuleGroupMetaOptions(RuleGroupMetaOptions):
    def __init__(self, group_name: str, attrs: dict) -> None:
        super().__init__(group_name, attrs)
        self.requisition_model = self.options.get("requisition_model")
        if self.requisition_model:
            if len(self.requisition_model.split(".")) != 2:  # noqa: PLR2004
                self.requisition_model = f"{self.app_label}.{self.requisition_model}"
                self.options.update(requisition_model=self.requisition_model)
            self.options.update(target_models=[self.requisition_model])
            rules = {k: v for k, v in attrs.items() if not k.startswith("_")}
            if self.requisition_model == self.source_model:
                for name, rule in rules.items():
                    if not rule.source_panel:
                        raise RequisitionRuleGroupMetaOptionsError(
                            f'Rule expects "source_panel". Got '
                            f'requisition_model="{self.requisition_model}", '
                            f'source_model="{self.source_model}". '
                            f"See {group_name}.{name}.",
                            code="source_panel_expected",
                        )
            else:
                for name, rule in rules.items():
                    if rule.source_panel:
                        raise RequisitionRuleGroupMetaOptionsError(
                            f'Rule does not expect "source_panel". Got '
                            f'requisition_model="{self.requisition_model}", '
                            f'source_model="{self.source_model}". '
                            f"See {group_name}.{name}.",
                            code="source_panel_not_expected",
                        )

    @property
    def default_meta_options(self) -> list[str]:
        opts = super().default_meta_options
        opts.extend(["requisition_model"])
        return opts


class RequisitionMetaclass(RuleGroupMetaclass):
    rule_group_meta = RequisitionRuleGroupMetaOptions


class RequisitionRuleGroup(RuleGroup, metaclass=RequisitionMetaclass):
    metadata_updater_cls = RequisitionMetadataUpdater

    @classmethod
    def requisitions_for_visit(cls, visit=None) -> RequisitionCollection:
        """Returns a list of scheduled or unscheduled
        Requisitions depending on visit_code_sequence.
        """
        if visit.visit_code_sequence != 0:
            requisitions = RequisitionCollection(
                *visit.visit.requisitions_unscheduled,
                *visit.visit.requisitions_prn,
                name="requisitions_for_visit",
            )
        else:
            requisitions = RequisitionCollection(
                *visit.visit.requisitions,
                *visit.visit.requisitions_prn,
                name="requisitions_for_visit",
            )
        return requisitions

    @classmethod
    def evaluate_rules(
        cls: Any,
        related_visit: RelatedVisitModel = None,
        allow_create: bool | None = None,
    ) -> tuple[dict[str, dict[str, list[RuleResult]]], dict[str, RequisitionMetadata]]:
        """Returns a tuple of (rule_results, metadata_objects) where
        rule_results ...

        Metadata must exist.
        """
        rule_results = {}
        metadata_objects = {}
        for rule in cls._meta.options.get("rules"):
            rule_results[str(rule)] = {}
            if result := rule.run(related_visit=related_visit):
                for target_model, entry_status in result.items():
                    rule_results[str(rule)].update({target_model: []})
                    for target_panel in rule.target_panels:
                        # only do something if target_panel is in
                        # visit.requisitions
                        if target_panel.name in [
                            r.panel.name for r in cls.requisitions_for_visit(related_visit)
                        ]:
                            metadata_updater = cls.metadata_updater_cls(
                                related_visit=related_visit,
                                source_model=target_model,
                                source_panel=target_panel,
                                allow_create=allow_create,
                            )
                            metadata_obj = metadata_updater.get_and_update(
                                entry_status=entry_status
                            )
                            metadata_objects.update({target_panel: metadata_obj})
                            rule_results[str(rule)][target_model].append(
                                RuleResult(target_panel, entry_status)
                            )
        return rule_results, metadata_objects
