from typing import Any

from django.contrib.sites.shortcuts import get_current_site
from django.db.models.aggregates import Count
from django.urls import reverse
from django.views.generic import TemplateView

from edc_action_item.models.action_item import ActionItem
from edc_constants.constants import CLOSED, NEW, OPEN
from edc_dashboard.view_mixins import EdcViewMixin
from edc_navbar import NavbarViewMixin

from ...constants import AE_TMG_ACTION
from ...utils import get_adverse_event_admin_site, get_adverse_event_app_label


class TmgHomeView(EdcViewMixin, NavbarViewMixin, TemplateView):
    template_name = "edc_adverse_event/tmg/tmg_home.html"
    navbar_selected_item = "tmg_home"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        death_report_changelist_url = reverse(
            f"{get_adverse_event_admin_site()}:{get_adverse_event_app_label()}_"
            f"deathreporttmg_changelist"
        )

        # summarize closed reports by site
        summary = (
            ActionItem.objects.filter(action_type__name=AE_TMG_ACTION, status=CLOSED)
            .values("site__name")
            .annotate(count=Count("status"))
            .order_by("site__name")
        )
        # summarize new and open for notice
        qs = (
            ActionItem.objects.filter(action_type__name=AE_TMG_ACTION, status__in=[NEW, OPEN])
            .exclude(site__name=get_current_site(request=self.request).name)
            .values("status", "site__name")
            .annotate(items=Count("status"))
        )
        notices = [
            (item.get("site__name"), item.get("status"), item.get("items"))
            for item in qs.order_by("status", "site__name")
        ]
        new_count = ActionItem.objects.filter(
            action_type__name=AE_TMG_ACTION,
            site__name=get_current_site(request=self.request).name,
            status=NEW,
        ).count()
        open_count = ActionItem.objects.filter(
            action_type__name=AE_TMG_ACTION,
            site__name=get_current_site(request=self.request).name,
            status=OPEN,
        ).count()
        closed_count = ActionItem.objects.filter(
            action_type__name=AE_TMG_ACTION,
            site__name=get_current_site(request=self.request).name,
            status=CLOSED,
        ).count()
        total_count = ActionItem.objects.filter(
            action_type__name=AE_TMG_ACTION,
            site__name=get_current_site(request=self.request).name,
            status__in=[NEW, OPEN, CLOSED],
        ).count()
        kwargs.update(
            {
                "new_count": new_count,
                "open_count": open_count,
                "closed_count": closed_count,
                "total_count": total_count,
                "summary": summary,
                "notices": notices,
                "death_report_changelist_url": death_report_changelist_url,
            }
        )
        return super().get_context_data(**kwargs)
