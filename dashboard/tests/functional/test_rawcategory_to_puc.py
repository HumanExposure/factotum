from uuid import uuid1

from django.test import TestCase
from django.urls import reverse
from django.utils.timezone import now
from django.contrib.auth.models import User

from dashboard.models import DataGroup, DataDocument, Product
from dashboard.views import RawCategoryToPUC, DataSource


class TestRawCategoryToPUCView(TestCase):
    path_name = "rawcategory_to_puc"
    minimum_document_count = 50

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="Karyn", password="specialP@55word"
        )
        cls.ds = DataSource.objects.create(title="Test DataGroup")
        cls.dg = DataGroup.objects.create(
            downloaded_at=now(), data_source=cls.ds, downloaded_by=cls.user
        )
        for min_visible_datadoc in range(cls.minimum_document_count):
            doc = DataDocument.objects.create(data_group=cls.dg, raw_category="visible")
            doc.product_set.add(Product.objects.create(upc=uuid1()))
        for max_hidden_datadoc in range(cls.minimum_document_count - 1):
            doc = DataDocument.objects.create(data_group=cls.dg, raw_category="hidden")
            doc.product_set.add(Product.objects.create(upc=uuid1()))

    def test_unauthorized(self):
        """ Verify that the page is unavailable to users who are not logged in
        """
        response = self.client.get(reverse(self.path_name), follow=True)
        self.assertRedirects(response, "/login/?next=" + reverse(self.path_name))

    def test_list_success(self):
        """ Test that GET requests to class return a page built using correct templates and contains correct data.
        """
        self.client.login(username="Karyn", password="specialP@55word")
        response = self.client.get(reverse(self.path_name))

        self.assertEqual(200, response.status_code)
        self.assertEqual(
            RawCategoryToPUC.as_view().__name__, response.resolver_match.func.__name__
        )
        self.assertTemplateUsed(response, template_name="core/base.html")
        self.assertTemplateUsed(
            response,
            template_name="product_curation/rawcategory/rawcategory_to_puc.html",
        )
        self.assertDictEqual(
            {
                "data_group__name": "",
                "raw_category": "visible",
                "document_count": self.minimum_document_count,
            },
            response.context["rows"][0],
        )

    def test_list_products_counted_once(self):
        """Add an additional product to a document.  Verify the document is only counted once
        """
        self.client.login(username="Karyn", password="specialP@55word")
        DataDocument.objects.filter(raw_category="visible").first().product_set.add(
            Product.objects.create(upc=uuid1())
        )
        response = self.client.get(reverse(self.path_name))

        self.assertDictEqual(
            {
                "data_group__name": "",
                "raw_category": "visible",
                "document_count": self.minimum_document_count,
            },
            response.context["rows"][0],
        )

    def test_list_documents_without_products_are_not_counted(self):
        """ Add a document without a product.  Verify it's not counted
        """
        self.client.login(username="Karyn", password="specialP@55word")
        DataDocument.objects.create(data_group=self.dg, raw_category="visible")
        response = self.client.get(reverse(self.path_name))

        self.assertDictEqual(
            {
                "data_group__name": "",
                "raw_category": "visible",
                "document_count": self.minimum_document_count,
            },
            response.context["rows"][0],
        )

    def test_list_documents_without_raw_categories_are_excluded(self):
        """ Add raw_categories that are blank and None and verify they are excluded
        """
        self.client.login(username="Karyn", password="specialP@55word")
        for blank_raw_category in range(self.minimum_document_count):
            doc = DataDocument.objects.create(data_group=self.dg, raw_category="")
            doc.product_set.add(Product.objects.create(upc=uuid1()))
        for null_raw_category in range(self.minimum_document_count):
            doc = DataDocument.objects.create(data_group=self.dg, raw_category=None)
            doc.product_set.add(Product.objects.create(upc=uuid1()))
        response = self.client.get(reverse(self.path_name))

        self.assertEqual(
            1,
            len(response.context["rows"]),
            'raw_categories of "blank" and "None" should be excluded',
        )
