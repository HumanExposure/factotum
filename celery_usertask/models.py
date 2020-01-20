from django.contrib.auth import get_user_model
from django.db import models


class UserTaskLog(models.Model):
    """Associates a task with the user who initialized it.

    Attributes:
        task: The UUID of the Celery task.
        user: The User model who initiated this task.
    """

    task = models.UUIDField(primary_key=True)
    name = models.CharField(max_length=255, db_index=True)
    user = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, db_index=True, null=True
    )
