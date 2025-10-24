from django.db import models
from django.db.models import Index


class NotificationMixin(models.Model):
    notification_plan_name = models.CharField(max_length=200)

    notification_datetime = models.DateTimeField()

    subject = models.CharField(max_length=200)

    recipient_list = models.TextField(null=True, default="")

    cc_list = models.TextField(null=True, default="")

    body = models.TextField(null=True, default="")

    status = models.CharField(
        max_length=15,
        default="new",
        choices=(("new", "New"), ("sent", "Sent"), ("cancelled", "Cancelled")),
    )

    sent = models.BooleanField(default=False)

    sent_datetime = models.DateTimeField(null=True)

    class Meta:
        abstract = True
        indexes = (Index(fields=["notification_datetime"]),)
