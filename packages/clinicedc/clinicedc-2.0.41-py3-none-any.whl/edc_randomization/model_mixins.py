from django.contrib.sites.models import Site
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import UniqueConstraint
from django_crypto_fields.fields import EncryptedCharField

from edc_model.models import HistoricalRecords
from edc_sites.managers import CurrentSiteManager

from .exceptions import RandomizationListModelError
from .randomizer import RandomizationError
from .site_randomizers import site_randomizers

__all__ = ["RandomizationListManager", "RandomizationListModelMixin"]


class RandomizationListManager(models.Manager):
    def get_by_natural_key(self, sid):
        return self.get(sid=sid)


class RandomizationListModelMixin(models.Model):
    """
    A model mixin for the randomization list.

    The default expects and ACTIVE vs PLACEBO randomization. If
    yours differs, you need to re-declare field "assignment"
    and model method "treatment_description". The default
    `Randomizer` class MAY also need to be customized.
    """

    assignment = EncryptedCharField()

    randomizer_name = models.CharField(max_length=50, default="default")

    subject_identifier = models.CharField(  # noqa: DJ001
        verbose_name="Subject Identifier", max_length=50, null=True, unique=True
    )

    sid = models.IntegerField(unique=True)

    site_name = models.CharField(max_length=100)

    allocation = EncryptedCharField(verbose_name="Original integer allocation", null=True)

    allocated = models.BooleanField(default=False)

    allocated_datetime = models.DateTimeField(null=True)

    allocated_user = models.CharField(max_length=50, default="")

    allocated_site = models.ForeignKey(
        Site, null=True, on_delete=models.PROTECT, related_name="+"
    )

    verified = models.BooleanField(default=False)

    verified_datetime = models.DateTimeField(null=True)

    verified_user = models.CharField(max_length=50, default="")

    objects = RandomizationListManager()

    history = HistoricalRecords(inherit=True)

    on_site = CurrentSiteManager("allocated_site")

    def __str__(self):
        return f"{self.site_name}.{self.sid} subject={self.subject_identifier}"

    def save(self, *args, **kwargs):
        self.randomizer_name = self.randomizer_cls.name
        try:
            self.assignment_description  # noqa: B018
        except RandomizationError as e:
            raise RandomizationListModelError(e) from e
        try:
            Site.objects.get(name=self.site_name)
        except ObjectDoesNotExist as e:
            site_names = [obj.name for obj in Site.objects.all()]
            raise RandomizationListModelError(
                f"Invalid site name. Got {self.site_name}. Expected one of {site_names}."
            ) from e
        super().save(*args, **kwargs)

    @property
    def short_label(self) -> str:
        return f"{self.assignment} SID:{self.site_name}.{self.sid}"

    @property
    def randomizer_cls(self):
        return site_randomizers.get(self.randomizer_name)

    # customize if approriate
    @property
    def assignment_description(self) -> str:
        """May be overridden."""
        if self.assignment not in self.randomizer_cls.assignment_map:
            raise RandomizationError(
                f"Invalid assignment. Expected one of "
                f"{list(self.randomizer_cls.assignment_map.keys())}. "
                f"Got `{self.assignment}`. See "
            )
        return self.assignment

    def natural_key(self):
        return (self.sid,)

    class Meta:
        abstract = True
        constraints = (
            UniqueConstraint(
                fields=["site_name", "sid"],
                name="%(app_label)s_%(class)s_site_sid_uniq",
            ),
        )
        permissions = (("display_assignment", "Can display assignment"),)
