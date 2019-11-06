from django.db import models


class QueryLog(models.Model):
    FACTOTUM = "FA"
    APPLICATION_CHOICES = [(FACTOTUM, "factotum")]
    query = models.CharField(max_length=255)
    user_id = models.PositiveIntegerField(null=True)
    application = models.CharField(max_length=2, choices=APPLICATION_CHOICES)
    time = models.DateTimeField(auto_now_add=True)
