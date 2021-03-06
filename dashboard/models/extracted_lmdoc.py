from django.db import models

from dashboard.models import ExtractedText


class ExtractedLMDoc(ExtractedText):
    STUDY_TYPE_CHOICES = (
        ("Targeted", "Targeted"),
        ("Non-Targeted", "Non-Targeted or Suspect Screening"),
        ("Other", "Other"),
    )

    study_type = models.CharField(
        "Study Type", choices=STUDY_TYPE_CHOICES, max_length=12, blank=True
    )

    media = models.CharField("Media", max_length=100, blank=True)

    def __str__(self):
        return str(self.data_document)
