from django.db import models
from django.utils.text import Truncator


class Comment(models.Model):
    email = models.EmailField(max_length=100)
    body = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.email) + ": " + Truncator(self.body).chars(100)
