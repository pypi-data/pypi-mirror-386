from django import forms
from django.core.exceptions import ObjectDoesNotExist

from edc_registration.models import RegisteredSubject

from ...models import StockRequestItem


class StockRequestItemForm(forms.ModelForm):
    def clean(self):
        cleaned_data = super().clean()
        try:
            RegisteredSubject.objects.get(
                subject_identifier=cleaned_data.get("subject_identifier"),
                consent_datetime__isnull=False,
                randomization_datetime__isnull=False,
            )
        except ObjectDoesNotExist as e:
            raise forms.ValidationError(
                {"subject_identifier": "Subject does not exist"}
            ) from e
        return cleaned_data

    class Meta:
        model = StockRequestItem
        fields = "__all__"
        help_text = {"request_item_identifier": "(read-only)"}  # noqa: RUF012
        widgets = {  # noqa: RUF012
            "request_item_identifier": forms.TextInput(attrs={"readonly": "readonly"}),
        }
