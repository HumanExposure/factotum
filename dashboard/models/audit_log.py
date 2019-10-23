from django.db import models
from django.conf import settings


class AuditLog(models.Model):
    object_key = models.PositiveIntegerField(null=True)
    model_name = models.CharField(max_length=128)
    field_name = models.CharField(max_length=128, db_index=True)
    old_value = models.TextField(null=True)
    new_value = models.TextField(null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    action = models.CharField(max_length=1)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, blank=True, null=True, on_delete=models.PROTECT
    )
