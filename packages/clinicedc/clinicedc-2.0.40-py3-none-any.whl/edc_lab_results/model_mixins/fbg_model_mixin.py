from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from edc_constants.choices import FASTING_CHOICES, YES_NO
from edc_constants.constants import FASTING
from edc_glucose.constants import GLUCOSE_HIGH_READING
from edc_lab.choices import RESULT_QUANTIFIER
from edc_lab.constants import EQ
from edc_reportable import (
    MILLIGRAMS_PER_DECILITER,
    MILLIMOLES_PER_LITER,
    MILLIMOLES_PER_LITER_DISPLAY,
)

from ..model_mixin_factories import reportable_result_model_mixin_factory


class FbgModelMixin(
    reportable_result_model_mixin_factory(
        utest_id="ifg",
        verbose_name="Blood Glucose (IFG)",
        units_choices=(
            (MILLIGRAMS_PER_DECILITER, MILLIGRAMS_PER_DECILITER),
            (MILLIMOLES_PER_LITER, MILLIMOLES_PER_LITER_DISPLAY),
        ),
        decimal_places=2,
        validators=[MinValueValidator(1.00), MaxValueValidator(GLUCOSE_HIGH_READING)],
    ),
    models.Model,
):
    """Impaired Fasting Glucose

    See edc-glucose for a newer version of this mixin.
    """

    is_poc = models.CharField(
        verbose_name="Was a point-of-care test used?",
        max_length=15,
        choices=YES_NO,
        default="",
    )
    fasting = models.CharField(
        verbose_name="Was this fasting or non-fasting?",
        max_length=25,
        choices=FASTING_CHOICES,
        default="",
        blank=False,
    )

    ifg_quantifier = models.CharField(
        max_length=10,
        choices=RESULT_QUANTIFIER,
        default=EQ,
    )

    def get_summary_options(self) -> dict:
        opts = super().get_summary_options()
        fasting = self.fasting == FASTING
        opts.update(fasting=fasting)
        return opts

    class Meta:
        abstract = True
