from django.db import models
from .common_info import CommonInfo
from .data_source import DataSource
from django.urls import reverse


class SourceCategory(CommonInfo):
    data_source = models.ForeignKey(
        DataSource, on_delete=models.CASCADE, help_text="data source"
    )
    title = models.CharField(max_length=200, null=False, blank=False, help_text="title")
    source_id = models.CharField(
        max_length=255, null=True, blank=True, help_text="source ID"
    )
    source_parent_id = models.CharField(
        max_length=255, null=True, blank=True, help_text="source parent ID"
    )
    path = models.CharField(max_length=255, null=True, blank=True, help_text="path")

    def __str__(self):
        return self.data_source.title + ", " + self.path

    def get_absolute_url(self):
        return reverse("source_category_edit", kwargs={"pk": self.pk})

    class Meta:
        verbose_name_plural = "Source categories"
