from django.db import models
from django.db.models.deletion import PROTECT
from django.utils import timezone

from edc_action_item.managers import (
    ActionIdentifierModelManager,
    ActionIdentifierSiteManager,
)
from edc_action_item.models import ActionModelMixin
from edc_constants.choices import YES_NO
from edc_identifier.model_mixins import NonUniqueSubjectIdentifierFieldMixin
from edc_model.models import ReportStatusModelMixin
from edc_model.validators import datetime_not_future
from edc_protocol.validators import datetime_not_before_study_start
from edc_sites.model_mixins import SiteModelMixin

from ...constants import DEATH_REPORT_TMG_ACTION, DEATH_REPORT_TMG_SECOND_ACTION
from ...models import CauseOfDeath
from ...utils import get_adverse_event_app_label


class DeathReportTmgManager(ActionIdentifierModelManager):
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(action_item__action_type__name=DEATH_REPORT_TMG_ACTION)


class DeathReportTmgSiteManager(ActionIdentifierSiteManager):
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(action_item__action_type__name=DEATH_REPORT_TMG_ACTION)


class DeathReportTmgSecondManager(ActionIdentifierModelManager):
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(action_item__action_type__name=DEATH_REPORT_TMG_SECOND_ACTION)


class DeathReportTmgSecondSiteManager(ActionIdentifierSiteManager):
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(action_item__action_type__name=DEATH_REPORT_TMG_SECOND_ACTION)


class DeathReportTmgFieldsModelMixin(models.Model):
    death_report = models.ForeignKey(
        f"{get_adverse_event_app_label()}.deathreport", on_delete=PROTECT
    )

    report_datetime = models.DateTimeField(
        verbose_name="Report Date",
        validators=[datetime_not_before_study_start, datetime_not_future],
        default=timezone.now,
    )

    cause_of_death = models.ForeignKey(
        CauseOfDeath,
        on_delete=PROTECT,
        verbose_name="Main cause of death",
        help_text=(
            "Main cause of death in the opinion of the local study doctor and local PI"
        ),
        null=True,
        default="",
    )

    cause_of_death_other = models.CharField(
        verbose_name='If "Other" above, please specify',
        max_length=100,
        blank=True,
        default="",
    )

    cause_of_death_agreed = models.CharField(
        verbose_name="Is the cause of death agreed between study doctor and TMG member?",
        max_length=15,
        choices=YES_NO,
        default="",
        help_text="If No, explain in the narrative below",
    )

    narrative = models.TextField(verbose_name="Narrative", blank=True, default="")

    class Meta:
        abstract = True


class DeathReportTmgMethodsModelMixin(models.Model):
    class Meta:
        abstract = True

    def __str__(self):
        return str(self.death_report)

    def save(self, *args, **kwargs):
        self.subject_identifier = self.death_report.subject_identifier
        super().save(*args, **kwargs)

    def natural_key(self):
        return (self.action_identifier,)

    natural_key.dependencies = ["edc_adverse_event.causeofdeath"]


class DeathReportTmgModelMixin(
    SiteModelMixin,
    ActionModelMixin,
    NonUniqueSubjectIdentifierFieldMixin,
    DeathReportTmgFieldsModelMixin,
    DeathReportTmgMethodsModelMixin,
    ReportStatusModelMixin,
    models.Model,
):
    action_name = DEATH_REPORT_TMG_ACTION

    objects = DeathReportTmgManager()

    on_site = DeathReportTmgSiteManager()

    class Meta(
        SiteModelMixin.Meta,
        NonUniqueSubjectIdentifierFieldMixin.Meta,
        ActionModelMixin.Meta,
    ):
        abstract = True
        verbose_name = "Death Report TMG (1st)"
        verbose_name_plural = "Death Report TMG (1st)"
        indexes = (
            *NonUniqueSubjectIdentifierFieldMixin.Meta.indexes,
            *ActionModelMixin.Meta.indexes,
            models.Index(fields=["subject_identifier", "action_identifier", "site", "id"]),
        )
