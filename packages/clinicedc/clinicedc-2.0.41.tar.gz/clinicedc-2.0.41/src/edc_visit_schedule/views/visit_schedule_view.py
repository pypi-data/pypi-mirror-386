from typing import Any

from django.views.generic.base import TemplateView

from edc_dashboard.view_mixins import EdcViewMixin
from edc_navbar.view_mixin import NavbarViewMixin

from ..site_visit_schedules import SiteVisitScheduleError, site_visit_schedules


class VisitScheduleView(EdcViewMixin, NavbarViewMixin, TemplateView):
    template_name = "edc_visit_schedule/visit_schedule.html"
    navbar_name = "edc_visit_schedule"
    navbar_selected_item = "visit_schedule"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        try:
            selected_visit_schedule = site_visit_schedules.get_visit_schedule(
                visit_schedule_name=self.kwargs.get("visit_schedule")
            )
        except SiteVisitScheduleError:
            selected_visit_schedule = None
        kwargs.update(
            {
                "visit_schedules": site_visit_schedules.registry,
                "selected_visit_schedule": selected_visit_schedule,
            }
        )
        return super().get_context_data(**kwargs)
