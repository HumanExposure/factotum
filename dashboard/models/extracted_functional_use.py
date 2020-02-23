from six import text_type

from django.db import models

from .common_info import CommonInfo
from .raw_chem import RawChem


class ExtractedFunctionalUse(CommonInfo, RawChem):
    pass

    @classmethod
    def detail_fields(cls):
        """Lists the fields to be displayed on a detail form

        Returns:
            list -- a list of field names
        """
        return ["extracted_text", "raw_chem_name", "raw_cas"]

    @classmethod
    def auditlog_fields(cls):
        """Needed, else inherited method from RawChem will apply with wrong fields"""
        return None

    def get_extractedtext(self):
        return self.extracted_text

    @property
    def data_document(self):
        return self.extracted_text.data_document

    def __get_label(self, field):
        return text_type(self._meta.get_field(field).verbose_name)
