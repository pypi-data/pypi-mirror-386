from edc_model_admin.admin_site import EdcAdminSite

from .apps import AppConfig

edc_pharmacy_admin = EdcAdminSite(
    name="edc_pharmacy_admin", app_label=AppConfig.name, keep_delete_action=True
)
edc_pharmacy_admin.disable_action("delete_selected")
