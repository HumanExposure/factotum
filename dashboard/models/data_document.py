from django.db import models
from .common_info import CommonInfo
from django.urls import reverse
from django.utils import timezone
from .document_type import DocumentType


class DataDocument(CommonInfo):

    filename = models.CharField(max_length=100)
    title = models.CharField(max_length=255)
    url = models.CharField(null=True, blank=True, max_length=200)
    raw_category = models.CharField(null=True, blank=True, max_length=50)
    data_group = models.ForeignKey('DataGroup', on_delete=models.CASCADE)
    products = models.ManyToManyField('Product', through='ProductDocument')
    matched = models.BooleanField(default=False)
    extracted = models.BooleanField(default=False)
    document_type = models.ForeignKey(DocumentType, on_delete=models.PROTECT, null=True, blank=True)
    organization = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return str(self.title)

    def get_absolute_url(self):
        return reverse('data_document', kwargs={'pk': self.pk})

    def get_abstract_filename(self):
        ext = self.filename.split('.')[-1] #maybe not all are PDF??
        return f'document_{self.pk}.{ext}'

    def pdf_url(self):
        dg = self.data_group.pk
        fn = self.get_abstract_filename()
        return f'/media/{dg}/pdf/{fn}'
