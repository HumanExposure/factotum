from django.db import models

from model_utils.models import TimeStampedModel
from .raw_chem import RawChem
from .extracted_text import ExtractedText

class ExtractedHHRec(TimeStampedModel, RawChem):
    media = models.CharField("Media", max_length=30,
                                        null=True, blank=True)
    sampling_method = models.TextField("Sampling Method", 
                                        null=True, blank=True)
    analytical_method = models.TextField("Analytical Method", 
                                        null=True, blank=True)
    num_measure = models.CharField("Numeric Measure", max_length=50,
                                        null=True, blank=True)
    num_nondetect = models.CharField("Numeric Nondetect", max_length=50,
                                        null=True, blank=True)                                    

    rawchem_ptr = models.OneToOneField(blank=False, null=False, 
            related_name='hhrecord',parent_link=True ,
            on_delete=models.CASCADE, to='dashboard.RawChem')


    @classmethod
    def detail_fields(cls):
        return ['raw_cas','raw_chem_name']

    def __str__(self):
        return self.raw_chem_name

    def get_datadocument_url(self):
        return self.extractedtext_ptr.data_document.get_absolute_url()

    @property
    def data_document(self):
        return self.extractedtext_ptr.data_document

    @property
    def extracted_hhdoc(self):
        return ExtractedText.objects.get_subclass(pk=self.extracted_text.data_document_id)