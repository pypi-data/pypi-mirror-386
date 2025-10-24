from __future__ import annotations

from typing import TYPE_CHECKING

from django.apps import apps as django_apps
from django.core.exceptions import ObjectDoesNotExist

from edc_visit_tracking.constants import MISSED_VISIT

from .metadata import Creator

if TYPE_CHECKING:
    from edc_model.models import BaseUuidModel
    from edc_sites.model_mixins import SiteModelMixin
    from edc_visit_tracking.model_mixins import VisitModelMixin as Base

    from .model_mixins.creates import CreatesMetadataModelMixin
    from .models import CrfMetadata, RequisitionMetadata

    class RelatedVisitModel(SiteModelMixin, CreatesMetadataModelMixin, Base, BaseUuidModel):
        pass


class MetadataHandlerError(Exception):
    pass


class MetadataObjectDoesNotExist(Exception):  # noqa: N818
    pass


class MetadataHandler:
    """A class to get or create a CRF metadata model instance."""

    creator_cls = Creator

    def __init__(
        self,
        metadata_model: str = None,
        related_visit: RelatedVisitModel = None,
        model: str = None,
        allow_create: bool | None = None,
    ):
        self.allow_create = True if allow_create is None else allow_create
        self.metadata_model: str = metadata_model
        self.model: str = model
        self.related_visit = related_visit
        self.creator = self.creator_cls(related_visit=self.related_visit, update_keyed=True)

    @property
    def metadata_model_cls(self) -> type[CrfMetadata] | type[RequisitionMetadata]:
        return django_apps.get_model(self.metadata_model)

    @property
    def metadata_obj(self) -> CrfMetadata | RequisitionMetadata:
        """Returns a metadata model instance.

        Creates if it does not exist and is allowed.
        """
        try:
            metadata_obj = self.metadata_model_cls.objects.get(**self.query_options)
        except ObjectDoesNotExist:
            # TODO: i think allow create should always be true 02/07/2025
            # if self.allow_create:
            metadata_obj = self._create()
            # else:
            #     raise MetadataObjectDoesNotExist(
            #         f"Unable to run metadata rule. Using {self.query_options}. Got `{e}`"
            #     )
        return metadata_obj

    def _create(self) -> CrfMetadata | RequisitionMetadata:
        """Returns a new metadata model instance for this CRF."""
        metadata_obj = None
        try:
            crf = next(
                f for f in self.creator.related_visit.visit.all_crfs if f.model == self.model
            )
        except StopIteration as e:
            if self.related_visit.reason != MISSED_VISIT:
                raise MetadataHandlerError(
                    "Create failed. Model not found. Not in visit.all_crfs. "
                    f"Model {self.model}. Got {e}"
                ) from e
        else:
            metadata_obj = self.creator.create_crf(crf)
        return metadata_obj

    @property
    def query_options(self) -> dict:
        """Returns a dict of options to query the `metadata` model.

        Note: the metadata model instance shares many field attributes
        with the visit model.
        """
        query_options = self.related_visit.metadata_query_options
        query_options.update(
            {
                "model": self.model,
                "subject_identifier": self.related_visit.subject_identifier,
            }
        )
        return query_options
