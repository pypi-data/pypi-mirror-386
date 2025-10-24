from django.contrib.auth.mixins import LoginRequiredMixin
from django.http.response import HttpResponseRedirect
from django.urls.base import reverse
from django.views.generic.base import View

from edc_dashboard.url_names import url_names
from edc_label.printers_mixin import PrintersMixin


class BaseRequisitionView(LoginRequiredMixin, PrintersMixin, View):
    success_url_name = "subject_dashboard_url"
    lab_home_url_name = "requisition_listboard_url"

    def get_success_url(self):
        return url_names.get(self.success_url_name)

    def get(self, request, *args, **kwargs):  # noqa: ARG002
        url = reverse(url_names.get(self.lab_home_url_name))
        return HttpResponseRedirect(url)

    def head(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def options(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)
