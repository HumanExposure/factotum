from uuid import uuid1

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils.timezone import now

from dashboard.forms import RawCategoryToPUCForm
from dashboard.models import DataSource, DataGroup, DataDocument, Product, PUC


class TestRawCategoryToPUCForm(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="Karyn", password="specialP@55word"
        )
        cls.ds = DataSource.objects.create(title="Test Data Source")
        cls.dg = DataGroup.objects.create(
            downloaded_at=now(),
            data_source=cls.ds,
            downloaded_by=cls.user,
            name="Test Data Group",
        )
        cls.doc = DataDocument.objects.create(data_group=cls.dg, raw_category="visible")
        cls.doc.product_set.add(Product.objects.create(upc=uuid1()))
        cls.puc = PUC.objects.create(last_edited_by=cls.user)

    def test_successful_form(self):
        """Test form can be validated and saved with valid data
        """
        form = RawCategoryToPUCForm(
            {
                "datagroup": self.dg.pk,
                "raw_category": self.doc.raw_category,
                "puc": self.puc.pk,
            }
        )

        self.assertTrue(form.is_valid())
        saved_response = form.save()
        self._assertProductToPucCreated(self.doc.products.all())
        self.assertEqual(saved_response["products_affected"], 1)

    def test_successful_form_duplicate_request(self):
        """New form submissions should override previous submissions
        """
        form = RawCategoryToPUCForm(
            {
                "datagroup": self.dg.pk,
                "raw_category": self.doc.raw_category,
                "puc": self.puc.pk,
            }
        )
        form2 = RawCategoryToPUCForm(
            {
                "datagroup": self.dg.pk,
                "raw_category": self.doc.raw_category,
                "puc": self.puc.pk,
            }
        )
        self.assertTrue(form.is_valid())
        form.save()
        self.assertTrue(form2.is_valid())
        saved_response = form2.save()
        self._assertProductToPucCreated(self.doc.products.all())
        self.assertEqual(saved_response["products_affected"], 1)

    def test_successful_form_reassign_puc(self):
        puc2 = PUC.objects.create(last_edited_by=self.user)
        form = RawCategoryToPUCForm(
            {
                "datagroup": self.dg.pk,
                "raw_category": self.doc.raw_category,
                "puc": self.puc.pk,
            }
        )
        form2 = RawCategoryToPUCForm(
            {
                "datagroup": self.dg.pk,
                "raw_category": self.doc.raw_category,
                "puc": puc2.pk,
            }
        )
        self.assertTrue(form.is_valid())
        form.save()
        self._assertProductToPucCreated(self.doc.products.all())
        self.assertTrue(form2.is_valid())
        saved_response = form2.save()
        self._assertProductToPucCreated(self.doc.products.all(), puc2)
        self.assertEqual(saved_response["products_affected"], 1)

    def test_successful_document_with_multiple_products(self):
        self.doc.product_set.add(Product.objects.create(upc=uuid1()))
        form = RawCategoryToPUCForm(
            {
                "datagroup": self.dg.pk,
                "raw_category": self.doc.raw_category,
                "puc": self.puc.pk,
            }
        )

        self.assertTrue(form.is_valid())
        saved_response = form.save()
        self._assertProductToPucCreated(self.doc.products.all())
        self.assertEqual(saved_response["products_affected"], 2)

    def test_successful_single_product_attached_to_different_documents(self):
        doc2 = DataDocument.objects.create(data_group=self.dg, raw_category="invalid")
        doc2.product_set.add(self.doc.product_set.first())
        form = RawCategoryToPUCForm(
            {
                "datagroup": self.dg.pk,
                "raw_category": self.doc.raw_category,
                "puc": self.puc.pk,
            }
        )

        self.assertTrue(form.is_valid())
        saved_response = form.save()
        self._assertProductToPucCreated(self.doc.products.all())
        self.assertEqual(saved_response["products_affected"], 1)

    def test_successful_resubmit_new_product(self):
        form = RawCategoryToPUCForm(
            {
                "datagroup": self.dg.pk,
                "raw_category": self.doc.raw_category,
                "puc": self.puc.pk,
            }
        )
        self.assertTrue(form.is_valid())
        form.save()

        self.doc.product_set.add(Product.objects.create(upc=uuid1()))
        form = RawCategoryToPUCForm(
            {
                "datagroup": self.dg.pk,
                "raw_category": self.doc.raw_category,
                "puc": self.puc.pk,
            }
        )
        self.assertTrue(form.is_valid())
        saved_response = form.save()
        self._assertProductToPucCreated(self.doc.products.all())
        self.assertEqual(saved_response["products_affected"], 2)

    def test_failure_blank_form(self):
        form = RawCategoryToPUCForm({})
        self.assertFalse(form.is_valid())
        self.assertDictEqual(
            form.errors,
            {
                "puc": ["This field is required."],
                "datagroup": ["This field is required."],
                "raw_category": ["This field is required."],
            },
        )

    def test_failure_incorrect_ids(self):
        form = RawCategoryToPUCForm(
            {"datagroup": 10000, "raw_category": "invalid", "puc": 10000}
        )
        self.assertFalse(form.is_valid())
        self.assertDictEqual(
            form.errors,
            {
                "puc": [
                    "Select a valid choice. "
                    "That choice is not one of the available choices."
                ],
                "datagroup": [
                    "Select a valid choice. "
                    "That choice is not one of the available choices."
                ],
                "raw_category": [
                    "Select a valid choice. "
                    "That choice is not one of the available choices."
                ],
            },
        )

    def test_failure_no_products(self):
        doc2 = DataDocument.objects.create(data_group=self.dg, raw_category=uuid1())
        form = RawCategoryToPUCForm(
            {
                "datagroup": self.dg.pk,
                "raw_category": doc2.raw_category,
                "puc": self.puc.pk,
            }
        )
        self.assertFalse(form.is_valid())
        self.assertDictEqual(
            form.errors, {"datagroup": ["No Products will be affected."]}
        )

    def test_failure_rawcategory_datagroup_mismatch(self):
        dg2 = DataGroup.objects.create(
            downloaded_at=now(),
            data_source=self.ds,
            downloaded_by=self.user,
            name="Test Data Group",
        )
        form = RawCategoryToPUCForm(
            {
                "datagroup": dg2.pk,
                "raw_category": self.doc.raw_category,
                "puc": self.puc.pk,
            }
        )
        self.assertFalse(form.is_valid())
        self.assertDictEqual(
            form.errors,
            {
                "raw_category": [
                    "No Documents with that Raw Category in the provided Data Group."
                ]
            },
        )

    def _assertProductToPucCreated(self, products, puc=None):
        """ Private method that checks to see that all products were attached
        to a specific PUC

        :param products: Queryset or List of products to be checked
        :param puc: PUC model or None to use the test PUC
        """
        puc = puc or self.puc  # if no puc is provided use the class puc
        product_to_puc = products[0].producttopuc_set.all()
        self.assertIsNotNone(products[0].puc_set.first(), "Product not assigned to PUC")
        self.assertEqual(
            puc,
            products[0].puc_set.first(),
            f"PUC with primary key {puc.pk} != PUC with primary key {products[0].puc_set.first().pk}",
        )
        self.assertEqual(product_to_puc.count(), 1)
        self.assertEqual(product_to_puc[0].classification_method, "BA")
