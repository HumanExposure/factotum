from six import text_type

from django.db import models
from django.core.exceptions import ValidationError

from .common_info import CommonInfo
from .extracted_text import ExtractedText


class ExtractedHabitsAndPracticesDataType(CommonInfo):
    title = models.CharField(max_length=50, blank=False, null=False)
    description = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.title


class ExtractedHabitsAndPractices(CommonInfo):
    extracted_text = models.ForeignKey(
        ExtractedText, on_delete=models.CASCADE, related_name="practices"
    )
    data_type = models.ForeignKey(
        ExtractedHabitsAndPracticesDataType, on_delete=models.PROTECT, null=True
    )
    product_surveyed = models.CharField("Product Surveyed", max_length=50)
    PUCs = models.ManyToManyField(
        "dashboard.PUC", through="dashboard.ExtractedHabitsAndPracticesToPUC"
    )
    mass = models.DecimalField(
        "Mass", max_digits=12, decimal_places=5, null=True, blank=True
    )
    mass_unit = models.CharField("Units for Mass", max_length=40, blank=True)
    frequency = models.DecimalField(
        "Frequency", max_digits=12, decimal_places=5, null=True, blank=True
    )
    frequency_unit = models.CharField("Units for Frequency", max_length=40, blank=True)
    duration = models.DecimalField(
        "Duration", max_digits=12, decimal_places=5, null=True, blank=True
    )
    duration_unit = models.CharField("Units for Duration", max_length=40, blank=True)
    prevalence = models.CharField("Prevalence", max_length=200, blank=True)
    notes = models.TextField("Notes", blank=True)

    def __str__(self):
        return self.product_surveyed

    @classmethod
    def detail_fields(cls):
        return [
            "product_surveyed",
            "mass",
            "mass_unit",
            "frequency",
            "frequency_unit",
            "duration",
            "duration_unit",
            "prevalence",
            "notes",
        ]

    def clean(self):
        if self.mass and self.mass_unit == "":
            msg = "Mass unit must be supplied if mass is specified."
            raise ValidationError({"mass_unit": msg})
        if self.frequency and self.frequency_unit == "":
            msg = "Frequency unit must be supplied if frequency is specified."
            raise ValidationError({"frequency_unit": msg})
        if self.duration and self.duration_unit == "":
            msg = "Duration unit must be supplied if duration is specified."
            raise ValidationError({"duration_unit": msg})

    def get_extractedtext(self):
        return self.extracted_text

    @property
    def data_document(self):
        return self.extracted_text.data_document

    def __get_label(self, field):
        return text_type(self._meta.get_field(field).verbose_name)

    @property
    def product_surveyed_label(self):
        return self.__get_label("product_surveyed")

    @property
    def mass_label(self):
        return self.__get_label("mass")

    @property
    def mass_unit_label(self):
        return self.__get_label("mass_unit")

    @property
    def frequency_label(self):
        return self.__get_label("frequency")

    @property
    def frequency_unit_label(self):
        return self.__get_label("frequency_unit")

    @property
    def duration_label(self):
        return self.__get_label("duration")

    @property
    def duration_unit_label(self):
        return self.__get_label("duration_unit")

    @property
    def prevalence_label(self):
        return self.__get_label("prevalence")

    @property
    def notes_label(self):
        return self.__get_label("notes")
