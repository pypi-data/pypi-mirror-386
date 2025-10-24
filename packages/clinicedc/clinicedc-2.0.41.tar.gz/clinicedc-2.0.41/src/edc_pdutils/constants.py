ACTION_ITEM_COLUMNS = [
    "action_identifier",
    "action_item_id",
    "action_item_reason",
    "parent_action_identifier",
    "parent_action_item_id",
    "related_action_identifier",
    "related_action_item_id",
]

SYSTEM_COLUMNS = [
    "created",
    "modified",
    "user_created",
    "user_modified",
    "hostname_created",
    "hostname_modified",
    "device_created",
    "device_modified",
    "locale_created",
    "locale_modified",
    "revision",
]

numeric_datatypes = [
    "DecimalField",
    "IntegerField",
    "BigIntegerField",
    "FloatField",
    "PositiveBigIntegerField",
    "PositiveIntegerField",
    "PositiveSmallIntegerField",
    "SmallIntegerField",
]

date_datatypes = ["DateTimeField", "DateField"]

timedelta_datatypes = ["DurationField"]
