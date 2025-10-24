from __future__ import annotations

from django.utils.translation import gettext_lazy as _


class TemplatesModelAdminMixin:
    """Override admin templates.

    Note: If using inlines.

    On the inline admin class specify the position `after` with class
    attribute `insert_after`:

    For example:
        class MyInlineModelAdmin(..):
            ...
            insert_after="<fieldname>"
            ...

    See also: https://linevi.ch/en/django-inline-in-fieldset.html
    """

    show_object_tools: bool = False
    view_on_site_label: str = _("View on site")
    history_label: str = _("Audit trail")
    show_history_label: bool = True

    add_form_template: str = "edc_model_admin/admin/change_form.html"
    change_form_template: str = "edc_model_admin/admin/change_form.html"
    change_list_template: str = "edc_model_admin/admin/change_list.html"
    change_list_title: str | None = None
    change_list_note: str | None = None
    change_list_help: str | None = None
    delete_confirmation_template: str = "edc_model_admin/admin/delete_confirmation.html"
    change_form_title: str | None = None

    def rendered_change_list_note(self):
        """Override if the class attr `change_list_note` is more than
        a normal string.

        For example, if the rendering attempts to resolve a URL for
        a class not yet registered, modeladmin registration silently
        stops registering the remaining modeladmin classes.
        """
        return self.change_list_note

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        extra_context.update(
            {
                "view_on_site_label": self.view_on_site_label,
                "show_history_label": self.show_history_label,
                "history_label": self.history_label,
                "title": self.change_form_title,
            }
        )
        return super().change_view(
            request, object_id, form_url=form_url, extra_context=extra_context
        )

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context if extra_context else {}
        extra_context.update(
            {
                "show_object_tools": self.show_object_tools,
                "change_list_note": self.rendered_change_list_note,
                "change_list_help": self.change_list_help,
            }
        )
        if self.change_list_title:
            extra_context.update({"title": self.change_list_title.title()})
        return super().changelist_view(request, extra_context=extra_context)
