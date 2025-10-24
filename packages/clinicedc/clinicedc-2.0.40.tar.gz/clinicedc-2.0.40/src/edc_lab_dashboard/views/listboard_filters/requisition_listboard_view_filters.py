from edc_lab.models import BoxItem
from edc_listboard.filters import ListboardFilter, ListboardViewFilters


def get_box_items():
    return BoxItem.objects.all().order_by("position").values("identifier")


class RequisitionListboardViewFilters(ListboardViewFilters):
    all = ListboardFilter(name="all", label="All", lookup={})

    received = ListboardFilter(label="Received", lookup={"received": True})

    not_received = ListboardFilter(
        label="Not Received", exclude_filter=True, lookup={"received": True}
    )

    processed = ListboardFilter(label="Processed", lookup={"processed": True})

    not_processed = ListboardFilter(
        label="Not processed", exclude_filter=True, lookup={"processed": True}
    )

    packed = ListboardFilter(label="Packed", lookup={"packed": True})

    not_packed = ListboardFilter(
        label="Not packed", exclude_filter=True, lookup={"packed": True}
    )
