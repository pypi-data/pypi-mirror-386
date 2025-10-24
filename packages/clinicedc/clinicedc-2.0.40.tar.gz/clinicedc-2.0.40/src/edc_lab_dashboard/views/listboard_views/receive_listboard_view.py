from __future__ import annotations

from typing import TYPE_CHECKING

from django.apps import apps as django_apps
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from edc_constants.constants import YES
from edc_dashboard.url_names import url_names

from .requisition_listboard_view import RequisitionListboardView

if TYPE_CHECKING:
    from django.db.models import Q

app_config = django_apps.get_app_config("edc_lab_dashboard")


class ReceiveListboardView(RequisitionListboardView):
    action_name = "receive"
    form_action_url = "receive_form_action_url"  # url_name
    listboard_template = "receive_listboard_template"
    listboard_url = "receive_listboard_url"  # url_name
    listboard_view_permission_codename = "edc_lab_dashboard.view_lab_receive_listboard"
    listboard_view_only_my_permission_codename = None
    navbar_selected_item = "receive"
    process_listboard_url = "process_listboard_url"  # url_name
    show_all = True
    search_form_url = "receive_listboard_url"  # url_name

    def get_queryset_filter_options(self, request, *args, **kwargs) -> tuple[Q, dict]:
        q_object, options = super().get_queryset_filter_options(request, *args, **kwargs)
        options.update(is_drawn=YES, clinic_verified=YES, received=False, processed=False)
        return q_object, options

    def get_empty_queryset_message(self) -> str:
        href = reverse(url_names.get(self.process_listboard_url))
        return format_html(
            "All specimens have been received. Continue to "
            '<a href="{}" class="alert-link">processing</a>',
            mark_safe(href),  # nosec B703, B308
        )
