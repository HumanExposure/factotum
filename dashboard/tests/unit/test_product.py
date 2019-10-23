from django.test import TestCase


from dashboard.tests.loader import fixtures_standard
from dashboard.models import ExtractedText, DataDocument, ProductDocument, Product


class ProductTestWithSeedData(TestCase):

    fixtures = fixtures_standard

    def test_rawchemlookup(self):
        # product with data document without extracted text
        et = ExtractedText.objects.values_list("pk", flat=True)
        dd = DataDocument.objects.exclude(pk__in=et).values_list("pk", flat=True)
        pd = ProductDocument.objects.filter(
            document__in=dd, product__isnull=False
        ).values_list("product", flat=True)
        p = Product.objects.filter(pk__in=pd).first()
        rawchems = [r for r in p.rawchems]
        self.assertEqual(rawchems, [])
