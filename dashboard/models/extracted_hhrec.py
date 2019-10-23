from six import text_type

from django.db import models

from .raw_chem import RawChem
from .common_info import CommonInfo
from .extracted_text import ExtractedText


class ExtractedHHRec(CommonInfo, RawChem):
    media = models.CharField("Media", max_length=30, null=True, blank=True)
    sampling_method = models.TextField("Sampling Method", null=True, blank=True)
    analytical_method = models.TextField("Analytical Method", null=True, blank=True)
    num_measure = models.CharField(
        "Numeric Measure", max_length=50, null=True, blank=True
    )
    num_nondetect = models.CharField(
        "Numeric Nondetect", max_length=50, null=True, blank=True
    )

    @classmethod
    def detail_fields(cls):
        return [
            "raw_chem_name",
            "raw_cas",
            "media",
            "num_measure",
            "num_nondetect",
            "sampling_method",
            "analytical_method",
        ]

    def get_datadocument_url(self):
        return self.extractedtext_ptr.data_document.get_absolute_url()

    @property
    def data_document(self):
        return self.extractedtext_ptr.data_document

    @property
    def extracted_hhdoc(self):
        return ExtractedText.objects.get_subclass(
            pk=self.extracted_text.data_document_id
        )

    def __get_label(self, field):
        return text_type(self._meta.get_field(field).verbose_name)

    @property
    def media_label(self):
        return self.__get_label("media")

    @property
    def sampling_method_label(self):
        return self.__get_label("sampling_method")

    @property
    def analytical_method_label(self):
        return self.__get_label("analytical_method")

    @property
    def num_measure_label(self):
        return self.__get_label("num_measure")

    @property
    def num_nondetect_label(self):
        return self.__get_label("num_nondetect")
