from __future__ import annotations

from typing import Any

from django.apps import apps as django_apps
from django.db import models

from edc_constants.constants import HIGH_PRIORITY
from edc_model.models import BaseUuidModel

from ..choices import PRIORITY
from ..exceptions import ActionTypeError

MISSING_ACTION_CLASS = "Model missing an action class. See {reference_model_cls!r}"
NOT_CONFIGURED_FOR_ACTIONS = (
    "Model not configured for Actions. Are you using the model mixin? "
    "See {reference_model_cls!r}. Got {err}"
)
REFERENCE_MODEL_LOOKUP_ERROR = "{err}. Got reference_model=`{reference_model}`"


class ActionTypeManager(models.Manager):
    use_in_migrations = True

    def get_by_natural_key(self, name):
        return self.get(name=name)


class ActionType(BaseUuidModel):
    name = models.CharField(max_length=50, unique=True)

    display_name = models.CharField(max_length=100)

    reference_model = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="reference model",
    )

    related_reference_model = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="origin reference model",
    )

    priority = models.CharField(max_length=25, choices=PRIORITY, default=HIGH_PRIORITY)

    show_on_dashboard = models.BooleanField(default=False)

    show_link_to_changelist = models.BooleanField(default=False)

    create_by_action = models.BooleanField(
        default=True, help_text="This action may be created by another action"
    )

    create_by_user = models.BooleanField(
        default=True, help_text="This action may be created by the user"
    )

    instructions = models.TextField(max_length=250, blank=True, default="")

    objects = ActionTypeManager()

    def __str__(self) -> str:
        return self.display_name

    def natural_key(self) -> tuple:
        return (self.name,)

    @property
    def reference_model_cls(self) -> Any:
        model_cls = None
        if self.reference_model:
            try:
                model_cls = django_apps.get_model(self.reference_model)
            except (LookupError, ValueError) as e:
                raise ActionTypeError(
                    REFERENCE_MODEL_LOOKUP_ERROR.format(
                        err=str(e), reference_model=self.reference_model
                    )
                ) from e
        return model_cls

    def save(self, *args, **kwargs):
        self.display_name = self.display_name or self.name
        if self.reference_model and self.reference_model != "edc_action_item.reference":
            try:
                if not self.reference_model_cls.action_name:
                    raise ActionTypeError(
                        MISSING_ACTION_CLASS.format(
                            reference_model_cls=self.reference_model_cls
                        )
                    )
            except AttributeError as e:
                if "action_name" in str(e):
                    raise ActionTypeError(
                        NOT_CONFIGURED_FOR_ACTIONS.format(
                            reference_model_cls=self.reference_model_cls, err=str(e)
                        )
                    ) from e
                raise
        super().save(*args, **kwargs)

    class Meta(BaseUuidModel.Meta):
        indexes = (
            *BaseUuidModel.Meta.indexes,
            models.Index(fields=["id", "name"]),
        )
        default_permissions = ("add", "change", "delete", "view", "export", "import")
