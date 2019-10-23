from six import text_type

from django.db import models

from .raw_chem import RawChem
from .common_info import CommonInfo


class ExtractedFunctionalUse(CommonInfo, RawChem):

    report_funcuse = models.CharField(
        "Reported functional use", max_length=255, null=True, blank=True
    )

    @classmethod
    def detail_fields(cls):
        return ["extracted_text", "raw_chem_name", "raw_cas", "report_funcuse"]

    def get_extractedtext(self):
        return self.extracted_text

    @property
    def data_document(self):
        return self.extracted_text.data_document

    def __get_label(self, field):
        return text_type(self._meta.get_field(field).verbose_name)

    @property
    def report_funcuse_label(self):
        return self.__get_label("report_funcuse")
