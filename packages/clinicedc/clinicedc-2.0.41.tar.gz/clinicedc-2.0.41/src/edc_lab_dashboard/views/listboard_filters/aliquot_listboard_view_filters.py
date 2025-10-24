from edc_lab.models import BoxItem
from edc_listboard.filters import ListboardFilter, ListboardViewFilters


def get_box_items():
    return BoxItem.objects.all().order_by("position").values("identifier")


class AliquotListboardViewFilters(ListboardViewFilters):
    all = ListboardFilter(name="all", label="All", lookup={})

    is_primary = ListboardFilter(label="Primary", lookup={"is_primary": True})

    packed = ListboardFilter(label="Packed", lookup={"aliquot_identifier__in": get_box_items})

    not_packed = ListboardFilter(
        label="Not Packed",
        exclude_filter=True,
        lookup={"aliquot_identifier__in": get_box_items},
    )

    shipped = ListboardFilter(label="Shipped", lookup={"shipped": True})

    not_shipped = ListboardFilter(label="Not shipped", default=True, lookup={"shipped": False})
