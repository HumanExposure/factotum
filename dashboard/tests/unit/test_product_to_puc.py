from django.test import TestCase, tag
from dashboard.tests.loader import load_model_objects
from dashboard.models import ProductToPUC
from dashboard.views.product_curation import ProductForm


@tag("loader")
class UberPUCTest(TestCase):
    def setUp(self):
        self.objects = load_model_objects()

    def test_uber_puc(self):
        # Test that when the product has no assigned PUC, the getter returns
        # None
        self.assertTrue(self.objects.p.uber_puc == None)

        self.ppuc = ProductToPUC.objects.create(
            product=self.objects.p,
            puc=self.objects.puc,
            puc_assigned_usr=self.objects.user,
        )

        # Test that the get_uber_product_to_puc method returns expected values
        uber_puc = self.objects.p.uber_puc
        _str = "Test General Category - Test Product Family - Test Product Type"
        self.assertEqual(_str, str(uber_puc))  # test str output
        uber_puc.prod_fam = None  # test str output *w/o* prod_fam
        _str = "Test General Category - Test Product Type"
        self.assertEqual(_str, str(uber_puc))
        uber_puc.gen_cat = None  # test str output *w/o* gen_cat or prod_fam
        _str = "Test Product Type"
        self.assertEqual(_str, str(uber_puc))


@tag("loader")
class Product_Form_Test(TestCase):
    def setUp(self):
        self.objects = load_model_objects()

    # it seems to be necessary to us the __dict__ and instance in order to load
    # the form for testing, w/o I don't think the fields are bound, which will
    # never validate!
    def test_ProductForm_invalid(self):
        form = ProductForm(self.objects.p.__dict__, instance=self.objects.p)
        self.assertFalse(form.is_valid())

    def test_ProductForm_valid(self):
        self.objects.p.title = "Title Necessary"
        self.objects.p.upc = "Upc Necessary"
        self.objects.p.document_type = self.objects.dt.id
        # print(self.objects.p)
        self.objects.p.save()
        form = ProductForm(self.objects.p.__dict__, instance=self.objects.p)
        # print(form.errors)
        self.assertTrue(form.is_valid())
