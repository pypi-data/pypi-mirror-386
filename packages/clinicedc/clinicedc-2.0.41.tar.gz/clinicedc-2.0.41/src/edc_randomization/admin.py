import contextlib

from django.conf import settings
from django.contrib import admin
from django.contrib.admin.sites import AlreadyRegistered
from django.contrib.sites.models import Site
from django.http import HttpResponseRedirect
from django.urls import reverse
from django_audit_fields.admin import audit_fields, audit_fieldset_tuple

from edc_label import Label
from edc_model_admin.mixins import TemplatesModelAdminMixin
from edc_protocol.research_protocol_config import ResearchProtocolConfig

from .admin_site import edc_randomization_admin
from .auth_objects import RANDO_UNBLINDED
from .blinding import user_is_blinded
from .site_randomizers import site_randomizers

__all__ = ["RandomizationListModelAdmin", "print_pharmacy_labels"]


@admin.action(permissions=["view"], description="Print labels for pharmacy")
def print_pharmacy_labels(modeladmin, request, queryset):
    zpl_data = []
    label = Label(
        label_template_name="rando_pharmacy_label.lbl",
        static_files_path="edc_pharmacy/label_templates",
    )
    for obj in queryset:
        context = dict(
            protocol=ResearchProtocolConfig().protocol,
            protocol_title=ResearchProtocolConfig().protocol_title,
            site=obj.site_name.upper(),
            subject_identifier=obj.subject_identifier,
            barcode_value=obj.sid,
            sid=obj.sid,
        )
        keys = [k for k in context]
        for fld in obj._meta.get_fields():
            if fld.name not in keys and fld.name != "assignment":
                context.update({fld.name: getattr(obj, fld.name)})
        zpl_data.append(
            str(label.render_as_zpl_data(copies=1, context=context, encoding=False))
            .strip("\n")
            .replace("\n", "")
        )
    request.session["zpl_data"] = "|".join(zpl_data)
    url = reverse("edc_label:browser_print_labels_url")
    return HttpResponseRedirect(url)


class RandomizationListModelAdmin(TemplatesModelAdminMixin, admin.ModelAdmin):
    list_per_page = 15

    actions = (print_pharmacy_labels,)

    view_on_site = False

    ordering = ("sid",)

    search_fields = ("subject_identifier", "sid")

    def get_fieldsets(self, request, obj=None):  # noqa: ARG002
        return (
            (None, {"fields": self.get_fieldnames(request)}),
            audit_fieldset_tuple,
        )

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super().get_readonly_fields(request, obj=obj)
        readonly_fields = (
            *readonly_fields,
            "subject_identifier",
            "sid",
            "site_name",
            "assignment",
            "allocated",
            "allocated_user",
            "allocated_datetime",
            "allocated_site",
            "randomizer_name",
            *audit_fields,
        )
        return tuple(set(readonly_fields))

    def get_queryset(self, request):
        """
        Filter the changelist to show for this site_name only.
        """
        site = Site.objects.get(pk=settings.SITE_ID)
        qs = self.model.objects.filter(site_name=site.name)
        ordering = self.get_ordering(request)
        if ordering:
            qs = qs.order_by(*ordering)
        return qs

    def get_list_display(self, request) -> tuple[str, ...]:
        fields = (
            "sid",
            "assignment",
            "site_name",
            "subject_identifier",
            "allocated_datetime",
            "allocated_site",
            "randomizer_name",
        )
        if flds := site_randomizers.get_by_model(
            self.model._meta.label_lower
        ).get_extra_list_display():
            fields = list(fields)
            for pos, fname in flds:
                fields.insert(pos, fname)
            fields = tuple(fields)
        if user_is_blinded(request.user.username) or (
            not user_is_blinded(request.user.username)
            and RANDO_UNBLINDED not in [g.name for g in request.user.groups.all()]
        ):
            fields = tuple([fname for fname in fields if fname != "assignment"])
        return fields

    @staticmethod
    def get_fieldnames(request) -> tuple[str, ...]:
        fields = (
            "subject_identifier",
            "sid",
            "assignment",
            "allocated",
            "allocated_user",
            "allocated_datetime",
            "allocated_site",
            "randomizer_name",
        )
        if user_is_blinded(request.user.username) or (
            not user_is_blinded(request.user.username)
            and RANDO_UNBLINDED not in [g.name for g in request.user.groups.all()]
        ):
            fields = tuple([fname for fname in fields if fname != "assignment"])
        return fields

    def get_list_filter(self, request) -> tuple[str, ...]:
        fields = (
            "assignment",
            "allocated_datetime",
            "allocated_site",
            "site_name",
            "randomizer_name",
        )
        if flds := site_randomizers.get_by_model(
            self.model._meta.label_lower
        ).get_extra_list_filter():
            fields = list(fields)
            for pos, fname in flds:
                fields.insert(pos, fname)
            fields = tuple(fields)
        if user_is_blinded(request.user.username) or (
            not user_is_blinded(request.user.username)
            and RANDO_UNBLINDED not in [g.name for g in request.user.groups.all()]
        ):
            fields = tuple([fname for fname in fields if fname != "assignment"])
        return fields


def register_admin():
    site_randomizers.autodiscover()
    for randomizer_cls in site_randomizers._registry.values():
        model = randomizer_cls.model_cls()
        admin_cls = type(f"{model.__name__}ModelAdmin", (RandomizationListModelAdmin,), {})
        with contextlib.suppress(AlreadyRegistered):
            edc_randomization_admin.register(model, admin_cls)


register_admin()
