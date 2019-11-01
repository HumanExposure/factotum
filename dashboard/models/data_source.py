from django.db import models
from .common_info import CommonInfo
from django.utils import timezone
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.core.validators import URLValidator


def validate_nonzero(value):
    if value == 0:
        raise ValidationError(
            _("Quantity {} is not allowed".format(value)), params={"value": value}
        )


class DataSource(CommonInfo):
    """A parent container for DataGroup objects"""

    STATE_CHOICES = (
        ("AT", "Awaiting Triage"),
        ("IP", "In Progress"),
        ("CO", "Complete"),
        ("ST", "Stale"),
    )

    PRIORITY_CHOICES = (("HI", "High"), ("MD", "Medium"), ("LO", "Low"))

    title = models.CharField(max_length=50)
    url = models.CharField(max_length=150, blank=True, validators=[URLValidator()])
    estimated_records = models.PositiveIntegerField(
        default=47, validators=[validate_nonzero]
    )
    state = models.CharField(max_length=2, choices=STATE_CHOICES, default="AT")
    description = models.TextField(null=True, blank=True)
    priority = models.CharField(max_length=2, choices=PRIORITY_CHOICES, default="HI")

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("data_source_edit", kwargs={"pk": self.pk})
