from uuid import uuid4

from django.db import models
from django.utils import timezone

from ...stock import ContainerType
from ..box import Box


class ContainerModelMixin(models.Model):
    container_identifier = models.CharField(max_length=36, default=uuid4, unique=True)

    container_datetime = models.DateTimeField(default=timezone.now)

    name = models.CharField(max_length=25, unique=True)

    container_type = models.ForeignKey(ContainerType, on_delete=models.PROTECT)

    box = models.ForeignKey(Box, on_delete=models.PROTECT, null=True)

    description = models.TextField(default="")

    contains_uniquely_identifiable_items = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.container_type.name} {self.name}"

    def save(self, *args, **kwargs):
        if not self.name:
            self.name = self.container_identifier
        super().save(*args, **kwargs)

    class Meta:
        abstract = True
        verbose_name = "Item"
        verbose_name_plural = "Items"
