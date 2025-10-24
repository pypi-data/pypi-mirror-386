from django.db import models

from edc_constants.choices import YES_NO

from ..models import DiastolicPressureField, SystolicPressureField
from ..utils import calculate_avg_bp


class SimpleBloodPressureModelMixin(models.Model):
    sys_blood_pressure = SystolicPressureField(
        null=True,
        blank=True,
    )

    dia_blood_pressure = DiastolicPressureField(
        null=True,
        blank=True,
    )

    class Meta:
        abstract = True


class BloodPressureModelMixin(models.Model):
    sys_blood_pressure_one = SystolicPressureField(
        verbose_name="Blood pressure: systolic (first reading)",
        null=True,
        blank=True,
    )

    dia_blood_pressure_one = DiastolicPressureField(
        verbose_name="Blood pressure: diastolic (first reading)",
        null=True,
        blank=True,
    )

    sys_blood_pressure_two = SystolicPressureField(
        verbose_name="Blood pressure: systolic (second reading)",
        null=True,
        blank=True,
    )

    dia_blood_pressure_two = DiastolicPressureField(
        verbose_name="Blood pressure: diastolic (second reading)",
        null=True,
        blank=True,
    )

    sys_blood_pressure_avg = models.IntegerField(
        verbose_name="Blood pressure: systolic (average)",
        null=True,
        blank=True,
    )

    dia_blood_pressure_avg = models.IntegerField(
        verbose_name="Blood pressure: diastolic (average)",
        null=True,
        blank=True,
    )

    # TODO: is this being validated

    severe_htn = models.CharField(
        verbose_name="Does the patient have severe hypertension?",
        max_length=15,
        choices=YES_NO,
        help_text="Based on the above readings. Severe HTN is any BP reading > 180/110mmHg",
        blank=True,
        default="",
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        (
            self.sys_blood_pressure_avg,
            self.dia_blood_pressure_avg,
        ) = calculate_avg_bp(**self.__dict__)
        super().save(*args, **kwargs)
