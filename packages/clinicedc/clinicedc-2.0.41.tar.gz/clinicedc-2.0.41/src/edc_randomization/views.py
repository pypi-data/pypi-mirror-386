from django.views.generic.base import TemplateView

from edc_dashboard.view_mixins import EdcViewMixin
from edc_navbar import NavbarViewMixin


class HomeView(EdcViewMixin, NavbarViewMixin, TemplateView):
    template_name = "edc_randomization/home.html"
    navbar_name = "edc_randomization"
    navbar_selected_item = "edc_randomization"
