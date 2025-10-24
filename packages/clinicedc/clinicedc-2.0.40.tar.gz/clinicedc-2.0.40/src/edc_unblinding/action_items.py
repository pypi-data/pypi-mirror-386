from edc_action_item.action_with_notification import ActionWithNotification
from edc_constants.constants import HIGH_PRIORITY, TBD, YES
from edc_offstudy.constants import END_OF_STUDY_ACTION

from .constants import UNBLINDING_REQUEST_ACTION, UNBLINDING_REVIEW_ACTION


class UnblindingRequestAction(ActionWithNotification):
    reference_model = "edc_unblinding.unblindingrequest"  # or inte_prn.unblindingrequest
    admin_site_name = "edc_unblinding_admin"  # or inte_prn_admin

    name = UNBLINDING_REQUEST_ACTION
    display_name = "Unblinding request"
    notification_display_name = " Unblinding request"
    parent_action_names = ()
    show_link_to_changelist = True
    show_link_to_add = True
    priority = HIGH_PRIORITY

    def get_next_actions(self):
        next_actions = []
        return self.append_to_next_if_required(
            next_actions=next_actions,
            action_name=UNBLINDING_REVIEW_ACTION,
            required=self.reference_obj.approved == TBD,
        )


class UnblindingReviewAction(ActionWithNotification):
    reference_model = "edc_unblinding.unblindingreview"  # or inte_prn.unblindingreview
    admin_site_name = "edc_unblinding_admin"  # or inte_prn_admin

    name = UNBLINDING_REVIEW_ACTION
    display_name = "Unblinding review pending"
    notification_display_name = " Unblinding review needed"
    parent_action_names = (UNBLINDING_REQUEST_ACTION,)
    show_link_to_changelist = True
    priority = HIGH_PRIORITY
    color_style = "info"
    create_by_user = False
    instructions = "This report is to be completed by the UNBLINDING REVIEWERS only."

    def get_next_actions(self):
        next_actions = []
        return self.append_to_next_if_required(
            next_actions=next_actions,
            action_name=END_OF_STUDY_ACTION,
            required=self.reference_obj.approved == YES,
        )
