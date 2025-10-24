from edc_action_item.action import Action
from edc_action_item.site_action_items import site_action_items
from edc_constants.constants import HIGH_PRIORITY
from edc_locator.utils import get_locator_model

SUBJECT_LOCATOR_ACTION = "submit-subject-locator"


# TODO: reference model name may not match that specified in visit schedule??
class SubjectLocatorAction(Action):
    name = SUBJECT_LOCATOR_ACTION
    display_name = "Submit Subject Locator"
    reference_model = get_locator_model()
    show_link_to_changelist = True
    admin_site_name = "edc_locator_admin"
    priority = HIGH_PRIORITY
    singleton = True


site_action_items.register(SubjectLocatorAction)
