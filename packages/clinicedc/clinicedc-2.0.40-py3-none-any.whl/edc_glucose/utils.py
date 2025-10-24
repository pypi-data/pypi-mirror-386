from decimal import Decimal

from django import forms

from edc_reportable import MILLIMOLES_PER_LITER, ConversionNotHandled
from edc_reportable.utils import convert_units
from edc_utils.round_up import round_half_away_from_zero

from .constants import GLUCOSE_HIGH_READING


def validate_glucose_as_millimoles_per_liter(
    prefix: str, cleaned_data: dict
) -> None | Decimal:
    converted_value = None
    min_val = Decimal("0.00")
    max_val = Decimal("30.00")
    high_value = Decimal(f"{GLUCOSE_HIGH_READING}")
    if (value := cleaned_data.get(f"{prefix}_value")) and (
        units := cleaned_data.get(f"{prefix}_units")
    ):
        try:
            converted_value = convert_units(
                label=prefix,
                value=value,
                units_from=units,
                units_to=MILLIMOLES_PER_LITER,
            )
        except ConversionNotHandled as e:
            raise forms.ValidationError({f"{prefix}_units": str(e)}) from e
        if (
            not (min_val <= round_half_away_from_zero(converted_value, 2) <= max_val)
            and round_half_away_from_zero(converted_value, 2) != high_value
        ):
            raise forms.ValidationError(
                {
                    f"{prefix}_value": (
                        f"This value is out-of-range. Got {converted_value} mmol/L"
                    )
                }
            )
    return converted_value
