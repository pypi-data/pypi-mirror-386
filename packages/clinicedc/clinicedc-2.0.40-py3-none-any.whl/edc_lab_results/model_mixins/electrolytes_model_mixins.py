from django.db import models

from edc_reportable import MILLIMOLES_PER_LITER_DISPLAY
from edc_reportable.units import MILLIGRAMS_PER_DECILITER, MILLIMOLES_PER_LITER

from ..model_mixin_factories import reportable_result_model_mixin_factory


class MagnesiumModelMixin(
    reportable_result_model_mixin_factory(
        utest_id="magnesium",
        verbose_name="Magnesium",
        units_choices=(
            (MILLIMOLES_PER_LITER, MILLIMOLES_PER_LITER_DISPLAY),
            (MILLIGRAMS_PER_DECILITER, MILLIGRAMS_PER_DECILITER),
        ),
        decimal_places=2,
    ),
    models.Model,
):
    class Meta:
        abstract = True


class PotassiumModelMixin(
    reportable_result_model_mixin_factory(
        utest_id="potassium",
        verbose_name="Potassium",
        units_choices=((MILLIMOLES_PER_LITER, MILLIMOLES_PER_LITER_DISPLAY),),
        decimal_places=1,
    ),
    models.Model,
):
    class Meta:
        abstract = True


class SodiumModelMixin(
    reportable_result_model_mixin_factory(
        utest_id="sodium",
        verbose_name="Sodium (Na)",
        units_choices=((MILLIMOLES_PER_LITER, MILLIMOLES_PER_LITER_DISPLAY),),
        decimal_places=0,
    ),
    models.Model,
):
    class Meta:
        abstract = True
