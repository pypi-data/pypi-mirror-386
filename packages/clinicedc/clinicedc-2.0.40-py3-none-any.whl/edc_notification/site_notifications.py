from __future__ import annotations

import copy
import sys
from json.decoder import JSONDecodeError
from typing import TYPE_CHECKING, Any

from django.apps import apps as django_apps
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.color import color_style
from django.utils.module_loading import import_module, module_has_submodule
from requests.exceptions import ConnectionError

from .mailing_list_manager import MailingListManager
from .utils import get_email_enabled

if TYPE_CHECKING:
    from edc_action_item.action_item_notification import ActionItemNotification
    from edc_action_item.models import ActionItem

    from .notification import Notification


style = color_style()


class AlreadyRegistered(Exception):
    pass


class RegistryNotLoaded(Exception):
    pass


class NotificationNotRegistered(Exception):
    pass


class SiteNotifications:
    def __init__(self):
        self._registry: dict[str, type[ActionItemNotification | Notification]] = {}
        self.loaded = False
        self.models = {}

    def __repr__(self):
        return f"{self.__class__.__name__}(loaded={self.loaded})"

    @property
    def registry(self):
        if not self.loaded:
            raise RegistryNotLoaded(
                "Registry not loaded. Is AppConfig for 'edc_notification' "
                "declared in settings?."
            )
        return self._registry

    def get(self, name) -> type[Notification]:
        """Returns a Notification by name."""
        if not self.loaded:
            raise RegistryNotLoaded(self)
        if not self._registry.get(name):
            raise NotificationNotRegistered(f"Notification not registered. Got '{name}'.")
        return self._registry.get(name)

    def register(self, notification_cls: type[Notification] = None):
        """Registers a Notification class unique by name."""
        self.loaded = True
        display_names = [n.display_name for n in self.registry.values()]
        if (
            notification_cls.name not in self.registry
            and notification_cls.display_name not in display_names
        ):
            self.registry.update({notification_cls.name: notification_cls})

            models = getattr(notification_cls, "models", [])
            if not models and getattr(notification_cls, "model", None):
                models = [notification_cls.model]
            for model in models:
                try:
                    if notification_cls.name not in [n.name for n in self.models[model]]:
                        self.models[model].append(notification_cls)
                except KeyError:
                    self.models.update({model: [notification_cls]})
        else:
            raise AlreadyRegistered(
                f"Notification {notification_cls.name}: "
                f"{notification_cls.display_name} is already registered."
            )

    def notify(self, instance: ActionItem = None, **kwargs):
        """A wrapper to call notification.notify for each notification
        class associated with the given model instance.

        Returns a dictionary of {notification.name: model, ...}
        including only notifications sent.
        """
        notified: dict[str, Any] = {}
        for notification_cls in self.registry.values():
            notification = notification_cls()
            if notification.notify(instance=instance, **kwargs):
                notified.update({notification_cls.name: instance._meta.label_lower})
        return notified

    def update_notification_list(
        self, apps: django_apps = None, schema_editor=None, verbose=False
    ):
        """Updates the notification model to ensure all registered
        notifications classes are listed.

        Typically called from a post_migrate signal.

        Also, in tests you can register a notification and the Notification
        class (not model) will automatically call this method if the
        named notification does not exist. See notification.notify()
        """
        notification_model_cls = (apps or django_apps).get_model(
            "edc_notification.notification"
        )

        # flag all notifications as disabled and re-enable as required
        notification_model_cls.objects.all().update(enabled=False)
        if site_notifications.loaded:
            if verbose:
                sys.stdout.write(style.MIGRATE_HEADING("Populating Notification model:\n"))
            self.delete_unregistered_notifications(apps=apps)
            for name, notification_cls in site_notifications.registry.items():
                if verbose:
                    sys.stdout.write(
                        f"  * Adding '{name}': '{notification_cls().display_name}'\n"
                    )
                try:
                    obj = notification_model_cls.objects.get(name=name)
                except ObjectDoesNotExist:
                    notification_model_cls.objects.create(
                        name=name,
                        display_name=notification_cls().display_name,
                        mailing_list_address=notification_cls().email_to[0],
                        enabled=True,
                    )
                else:
                    obj.display_name = notification_cls().display_name
                    obj.mailing_list_address = notification_cls().email_to[0]
                    obj.enabled = True
                    obj.save()

    @staticmethod
    def delete_unregistered_notifications(apps: django_apps = None):
        """Delete orphaned notification model instances."""
        notification_model_cls = (apps or django_apps).get_model(
            "edc_notification.notification"
        )
        return notification_model_cls.objects.exclude(
            name__in=[n.name for n in site_notifications.registry.values()]
        ).delete()

    def create_mailing_lists(self, verbose=True):
        """Creates the mailing list for each registered notification."""
        responses = {}
        if (
            get_email_enabled()
            and self.loaded
            and settings.EMAIL_BACKEND != "django.core.mail.backends.locmem.EmailBackend"
        ):
            sys.stdout.write(style.MIGRATE_HEADING("Creating mailing lists:\n"))
            for name, notification_cls in self.registry.items():
                notification = notification_cls()
                manager = MailingListManager(
                    address=notification.email_to,
                    name=notification.name,
                    display_name=notification.display_name,
                )
                try:
                    response = manager.create()
                except ConnectionError as e:
                    sys.stdout.write(
                        style.ERROR(f"  * Failed to create mailing list {name}. Got {e}\n")
                    )
                else:
                    if verbose:
                        try:
                            message = response.json().get("message")
                        except JSONDecodeError:
                            message = response.text
                        sys.stdout.write(
                            f"  * Creating mailing list {name}. "
                            f'Got {response.status_code}: "{message}"\n'
                        )
                    responses.update({name: response})
        return responses

    @staticmethod
    def autodiscover(module_name: str = None, verbose: bool | None = False):
        """Autodiscovers classes in the notifications.py file of any
        INSTALLED_APP.
        """
        module_name = module_name or "notifications"
        verbose = True if verbose is None else verbose
        sys.stdout.write(f" * checking for {module_name} ...\n")
        for app in django_apps.app_configs:
            before_import_registry = None
            try:
                mod = import_module(app)
                try:
                    before_import_registry = copy.copy(site_notifications._registry)
                    import_module(f"{app}.{module_name}")
                    if verbose:
                        sys.stdout.write(
                            f"   - registered notifications from application '{app}'\n"
                        )
                except Exception as e:
                    if f"No module named '{app}.{module_name}'" not in str(e):
                        site_notifications._registry = before_import_registry
                        if module_has_submodule(mod, module_name):
                            raise
            except ModuleNotFoundError:
                pass


site_notifications = SiteNotifications()
