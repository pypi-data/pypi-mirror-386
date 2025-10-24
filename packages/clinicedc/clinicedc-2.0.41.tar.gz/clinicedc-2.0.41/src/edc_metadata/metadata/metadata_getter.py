from __future__ import annotations

from typing import TYPE_CHECKING, Any
from warnings import warn

from django.apps import apps as django_apps
from django.contrib.admin.sites import all_sites
from django.core.exceptions import MultipleObjectsReturned
from django.db.models import QuerySet

from .metadata import model_cls_registered_with_admin_site

if TYPE_CHECKING:
    from edc_appointment.models import Appointment
    from edc_visit_tracking.typing_stubs import RelatedVisitProtocol

    from ..models import CrfMetadata, RequisitionMetadata


class MetadataGetterError(Exception):
    pass


class MetadataValidator:
    def __init__(
        self,
        metadata_obj: CrfMetadata | RequisitionMetadata,
        related_visit: RelatedVisitProtocol,
    ) -> None:
        self.metadata_obj = metadata_obj
        self.related_visit = related_visit
        self.validate_metadata_object()

    @property
    def extra_query_attrs(self) -> dict:
        return {}

    def validate_metadata_object(self) -> None:
        if self.metadata_obj:
            # confirm model class exists
            try:
                source_model_cls = django_apps.get_model(self.metadata_obj.model)
            except LookupError:
                self.metadata_obj.delete()
                self.metadata_obj = None
            else:
                if not model_cls_registered_with_admin_site(source_model_cls):
                    warn(
                        "Model class not registered with Admin. "
                        f"Deleting related metadata. Got {source_model_cls}.",
                        stacklevel=2,
                    )
                    self.metadata_obj.delete()
                    self.metadata_obj = None
                else:
                    # confirm metadata.entry_status is correct
                    query_attrs = {
                        f"{source_model_cls.related_visit_model_attr()}": self.related_visit
                    }
                    query_attrs.update(**self.extra_query_attrs)
                    if source_model_cls.objects.filter(**query_attrs).values("id").count() > 1:
                        raise MultipleObjectsReturned(
                            f"{source_model_cls._meta.label_lower} {self.related_visit}"
                        )
                    # try:
                    #     model_cls.objects.get(**query_attrs)
                    # except AttributeError as e:
                    #     if "related_visit_model_attr" not in str(e):
                    #         raise ImproperlyConfigured(f"{e} See {repr(model_cls)}")
                    #     raise
                    # except ObjectDoesNotExist:
                    #     pass
                    # except MultipleObjectsReturned:
                    #     raise

    @staticmethod
    def model_cls_registered_with_admin_site(model_cls: Any) -> bool:
        """Returns True if model cls is registered in Admin."""
        return any(model_cls in admin_site._registry for admin_site in all_sites)


class MetadataGetter:
    """A class that gets a filtered queryset of metadata --
    `metadata_objects`.

    * gets a queryset of CrfMetadata/RequisitionMetadata instances for
      the given appointment;
    * validates the entry status of each using the
      `metadata_validator_cls` and;
    * returns a requeried queryset.
    """

    metadata_model: str = None

    metadata_validator_cls = MetadataValidator

    def __init__(self, appointment: Appointment) -> None:
        self.options = {}
        self.appointment = appointment
        self.related_visit: RelatedVisitProtocol | None = getattr(
            self.appointment, "related_visit", None
        )
        instance = self.related_visit or self.appointment
        self.subject_identifier = instance.subject_identifier
        self.visit_code = instance.visit_code
        self.visit_code_sequence = instance.visit_code_sequence
        query_options = dict(
            subject_identifier=self.subject_identifier,
            visit_code=self.visit_code,
            visit_code_sequence=self.visit_code_sequence,
            visit_schedule_name=instance.visit_schedule_name,
            schedule_name=instance.schedule_name,
        )
        queryset = self.metadata_model_cls.objects.filter(**query_options).order_by(
            "show_order"
        )
        self.metadata_objects = self.validate_metadata_objects(queryset)

    @property
    def metadata_model_cls(self) -> CrfMetadata | RequisitionMetadata:
        return django_apps.get_model(self.metadata_model)

    def next_object(
        self, show_order: int | None = None, entry_status: str | None = None
    ) -> CrfMetadata | RequisitionMetadata:
        """Returns the next model instance based on the show order."""
        if show_order is None:
            metadata_obj = None
        else:
            opts = {"show_order__gt": show_order}
            if entry_status:
                opts.update(entry_status=entry_status)
            metadata_obj = self.metadata_objects.filter(**opts).order_by("show_order").first()
        return metadata_obj

    def validate_metadata_objects(
        self, queryset: QuerySet[CrfMetadata | RequisitionMetadata]
    ) -> QuerySet[CrfMetadata | RequisitionMetadata]:
        metadata_obj: CrfMetadata | RequisitionMetadata
        for metadata_obj in queryset:
            self.metadata_validator_cls(metadata_obj, self.related_visit)
        return queryset.all()
