from __future__ import annotations

from typing import TYPE_CHECKING

from django.core.exceptions import ObjectDoesNotExist

from .exceptions import SingletonActionItemError
from .get_action_type import get_action_type

if TYPE_CHECKING:
    from .action import Action
    from .models import ActionItem


def create_action_item(
    action_cls: type[Action],
    subject_identifier: str = None,
    action_identifier: str | None = None,
    related_action_item: ActionItem | None = None,
    parent_action_item: ActionItem | None = None,
    priority: bool | None = None,
    using: str | None = None,
    site_id: int | None = None,
    **kwargs,
) -> ActionItem:
    action_item = None
    if action_cls.singleton:
        try:
            action_item = (
                action_cls.action_item_model_cls()
                .objects.using(using)
                .get(
                    action_type=get_action_type(action_cls),
                    subject_identifier=subject_identifier,
                )
            )
        except ObjectDoesNotExist:
            pass
        else:
            raise SingletonActionItemError(
                f"Action {action_cls.name} can only be "
                f"created once per subject. Got {subject_identifier}."
            )
    if not action_item:
        opts = dict(
            subject_identifier=subject_identifier,
            action_type=get_action_type(action_cls),
            action_identifier=action_identifier,
            linked_to_reference=False,
            priority=priority,
        )
        if parent_action_item:
            opts.update(parent_action_item=parent_action_item)
        if related_action_item:
            opts.update(related_action_item=related_action_item)
        if site_id:
            opts.update(site_id=site_id)
        action_item = action_cls.action_item_model_cls()(**opts)
        action_item.save(using=using)
        action_item.refresh_from_db()
    return action_item
