import json
from uuid import uuid1

from django.test import TestCase
from django.urls import reverse
from django.utils.timezone import now
from django.contrib.auth.models import User

from dashboard.models import DataGroup, DataDocument, Product
from dashboard.views import DataSource, PUC, RawCategoryToPUCList


class TestRawCategoryToPUCView(TestCase):
    path_name = "rawcategory_to_puc"
    minimum_document_count = 50
    docs = []

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
        for min_visible_datadoc in range(cls.minimum_document_count):
            cls.doc = DataDocument.objects.create(
                data_group=cls.dg, raw_category="visible"
            )
            cls.doc.product_set.add(Product.objects.create(upc=uuid1()))
            cls.docs.append(cls.doc)
        cls.puc = PUC.objects.create(last_edited_by=cls.user)

        cls.success_row_context = {
            "data_group__id": cls.dg.pk,
            "data_group__name": cls.dg.name,
            "raw_category": cls.docs[0].raw_category,
            "document_count": cls.minimum_document_count,
        }

    def test_list_unauthorized(self):
        """ Verify that the list page is unavailable to users who are not logged in
        """
        response = self.client.get(reverse(self.path_name), follow=True)
        self.assertRedirects(response, "/login/?next=" + reverse(self.path_name))

    def test_post_unauthorized(self):
        """ Verify that the list page is unavailable to users who are not logged in
        """
        response = self.client.post(reverse(self.path_name), follow=True)
        self.assertRedirects(response, "/login/?next=" + reverse(self.path_name))

    def test_list_success(self):
        """ Test that GET requests to class return a page built using correct templates and contains correct data.
        """
        self.client.login(username="Karyn", password="specialP@55word")
        response = self.client.get(reverse(self.path_name))

        self.assertEqual(200, response.status_code)
        self.assertEqual(
            RawCategoryToPUCList.as_view().__name__,
            response.resolver_match.func.__name__,
        )
        self.assertTemplateUsed(response, template_name="core/base.html")
        self.assertTemplateUsed(
            response,
            template_name="product_curation/rawcategory/rawcategory_to_puc.html",
        )
        self.assertDictEqual(
            self.success_row_context, response.context["object_list"][0]
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
            self.success_row_context, response.context["object_list"][0]
        )

    def test_list_documents_without_products_are_not_counted(self):
        """ Add a document without a product.  Verify it's not counted
        """
        self.client.login(username="Karyn", password="specialP@55word")
        DataDocument.objects.create(data_group=self.dg, raw_category="visible")
        response = self.client.get(reverse(self.path_name))

        self.assertDictEqual(
            self.success_row_context, response.context["object_list"][0]
        )

    def test_list_groups_under_minimum_not_shown(self):
        """Add an additional product to a document.  Verify the document is only counted once
        """
        self.client.login(username="Karyn", password="specialP@55word")
        DataDocument.objects.filter(raw_category="visible").first().delete()
        response = self.client.get(reverse(self.path_name))

        self.assertEqual(
            0,
            len(response.context["object_list"]),
            f"Data Groups with less than {self.minimum_document_count} documents should be excluded",
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
            len(response.context["object_list"]),
            'raw_categories of "blank" and "None" should be excluded',
        )

    def test_post_success_single_group(self):
        """ Verify products are attached to pucs for provided datagroup
        """
        self.client.login(username="Karyn", password="specialP@55word")
        response = self.client.post(
            reverse(self.path_name),
            {
                "datagroup_rawcategory_groups": json.dumps(
                    [{"raw_category": self.doc.raw_category, "datagroup": self.dg.pk}]
                ),
                "puc": self.puc.pk,
            },
            follow=True,
        )

        for products in [document.products.all() for document in self.docs]:
            self._assertProductToPucCreated(products)
        self.assertDictEqual(
            self.success_row_context, response.context["object_list"][0]
        )
        # Verify a success message was returned after redirect.  Message content not specified.
        self.assertEqual(len(response.context["success_messages"]), 1)

    def test_post_success_multiple_groups(self):
        """ Verify products are attached to pucs for multiple provided datagroups
        """
        dg2 = DataGroup.objects.create(
            downloaded_at=now(),
            data_source=self.ds,
            downloaded_by=self.user,
            name="Test Data Group 2",
        )
        docs2 = []
        for min_visible_datadoc in range(self.minimum_document_count):
            doc2 = DataDocument.objects.create(data_group=dg2, raw_category="visible 2")
            doc2.product_set.add(Product.objects.create(upc=uuid1()))
            docs2.append(doc2)

        self.client.login(username="Karyn", password="specialP@55word")
        response = self.client.post(
            reverse(self.path_name),
            {
                "datagroup_rawcategory_groups": json.dumps(
                    [
                        {
                            "raw_category": self.doc.raw_category,
                            "datagroup": self.dg.pk,
                        },
                        {"raw_category": doc2.raw_category, "datagroup": dg2.pk},
                    ]
                ),
                "puc": self.puc.pk,
            },
            follow=True,
        )

        # self.assertEqual(response.status_code, 201)
        for products in [document.products.all() for document in self.docs]:
            self._assertProductToPucCreated(products)
        for products in [document.products.all() for document in docs2]:
            self._assertProductToPucCreated(products)
        # Verify a success message was returned after redirect.  Message content not specified.
        self.assertEqual(len(response.context["success_messages"]), 2)

    def test_post_required_fields(self):
        """ Verify errors are returned if required forms are not provided
        """
        self.client.login(username="Karyn", password="specialP@55word")
        response_no_datagroup = self.client.post(
            reverse(self.path_name), {}, follow=True
        )
        response_no_puc = self.client.post(
            reverse(self.path_name),
            {
                "datagroup_rawcategory_groups": json.dumps(
                    [{"raw_category": self.doc.raw_category, "datagroup": self.dg.pk}]
                )
            },
            follow=True,
        )

        self.assertDictEqual(
            {"error_group": "No Rows Selected"},
            response_no_datagroup.context["form_errors"][0],
        )
        self.assertDictEqual(
            {
                "error_group": f"Data Group: {self.dg.pk} - visible",
                "error_list": {"puc": ["This field is required."]},
            },
            response_no_puc.context["form_errors"][0],
        )

    def test_post_already_attached(self):
        """ Verify products are attached to pucs for provided datagroup
        """
        self.client.login(username="Karyn", password="specialP@55word")
        self.client.post(
            reverse(self.path_name),
            {
                "datagroup_rawcategory_groups": json.dumps(
                    [{"raw_category": self.doc.raw_category, "datagroup": self.dg.pk}]
                ),
                "puc": self.puc.pk,
            },
        )
        for products in [document.products.all() for document in self.docs]:
            self._assertProductToPucCreated(products)
        puc2 = PUC.objects.create(last_edited_by=self.user)
        self.client.post(
            reverse(self.path_name),
            {
                "datagroup_rawcategory_groups": json.dumps(
                    [{"raw_category": self.doc.raw_category, "datagroup": self.dg.pk}]
                ),
                "puc": puc2.pk,
            },
        )
        for products in [document.products.all() for document in self.docs]:
            self._assertProductToPucCreated(products, puc2)

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
