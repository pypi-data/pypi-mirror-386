from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from edc_constants.choices import YES_NO
from edc_glucose.model_mixin_factories import fasting_model_mixin_factory
from edc_reportable.units import MICRO_IU_MILLILITER, MICRO_IU_MILLILITER_DISPLAY

from ..model_mixin_factories import reportable_result_model_mixin_factory


class InsulinModelMixin(
    reportable_result_model_mixin_factory(
        utest_id="ins",
        verbose_name="Insulin",
        units_choices=((MICRO_IU_MILLILITER, MICRO_IU_MILLILITER_DISPLAY),),
        validators=[MinValueValidator(0.0), MaxValueValidator(999.0)],
    ),
    fasting_model_mixin_factory(
        None,
        field_options={"fasting": dict(choices=YES_NO, default=None)},
        fasting=models.CharField(
            verbose_name="Has the participant fasted?",
            max_length=15,
            choices=YES_NO,
            null=True,
            blank=False,
            help_text="As reported by patient",
        ),
    ),
    models.Model,
):
    class Meta:
        abstract = True
