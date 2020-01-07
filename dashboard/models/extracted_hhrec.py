from django.db import models
from six import text_type

from .common_info import CommonInfo
from .extracted_text import ExtractedText
from .raw_chem import RawChem


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
        """Lists the fields to be displayed on a detail form

        Returns:
            list -- a list of field names
        """
        return [
            "raw_chem_name",
            "raw_cas",
            "media",
            "num_measure",
            "num_nondetect",
            "sampling_method",
            "analytical_method",
        ]

    @classmethod
    def auditlog_fields(cls):
        """Lists the fields to be included in the audit log triggers

        Returns:
            list -- a list of field names
        """
        return [
            "media",
            "sampling_method",
            "analytical_method",
            "num_measure",
            "num_nondetect",
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

    @property
    def auditlog_model_name(self):
        """
        Returns the string that is used in the AuditLog table in the
        'model_name' field
        """
        return "extractedhhrec"
