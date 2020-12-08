import os
from lxml import html
from django.urls import reverse

from django.test import TransactionTestCase, override_settings, TestCase
from dashboard.models import DataDocument, Product, ProductToPUC, PUC
from dashboard.tests.loader import fixtures_standard, load_producttopuc
from django.core.exceptions import ObjectDoesNotExist


@override_settings(ALLOWED_HOSTS=["testserver"])
class TestProductDetail(TestCase):
    fixtures = fixtures_standard

    def setUp(self):
        self.client.login(username="Karyn", password="specialP@55word")

    @classmethod
    def setUpTestData(cls):
        # Set up data for the whole TestCase
        load_producttopuc()

    def test_anonymous_read(self):
        self.client.logout()
        response = self.client.get("/product/11/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "<title>Product 11: 3M(TM) Rubber &amp; Vinyl 80 Spray Adhesive</title>",
        )

    def test_anonymous_edit_not_allowed(self):
        self.client.logout()
        response = self.client.post("/product/edit/1/", {"title": "not allowed"})
        self.assertEqual(response.status_code, 302)

    def test_anonymous_delete_not_allowed(self):
        self.client.logout()
        response = self.client.post("/product/delete/1/")
        self.assertEqual(response.status_code, 302)

    def test_product_delete(self):
        self.assertTrue(Product.objects.get(pk=11), "Product 11 should exist")
        response = self.client.get("/product/delete/11/")
        with self.assertRaises(ObjectDoesNotExist):
            Product.objects.get(pk=11)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/datadocument/163194/")

    def test_product_update(self):
        p = Product.objects.get(pk=11)
        self.client.post(
            f"/product/edit/11/",
            {
                "title": "x",
                "manufacturer": "",
                "brand_name": "",
                "short_description": "none",
                "long_description": "none",
                "size": "",
                "color": "",
                "model_number": "2",
                "url": "https://www.google.com",
            },
        )
        p.refresh_from_db()
        self.assertEqual(p.title, "x", 'Product 11 should have the title "x"')
        self.assertEqual(
            p.url,
            "https://www.google.com",
            'Product 11 should have the url "https://www.google.com"',
        )

    def test_url_detail(self):
        self.test_product_update()
        response = self.client.get("/product/11/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "View product source (external)")

    def test_hover_definition(self):
        p = Product.objects.get(pk=11)
        response = self.client.get(f"/product/{p.pk}/")
        lxml = html.fromstring(response.content.decode("utf8"))
        for tag in p.get_puc_tags():
            elem = lxml.xpath(f'//li[@data-tag-name="{tag.name}"]')
            if not elem:
                elem = lxml.xpath(f'//button[@data-tag-name="{tag.name}"]')
            self.assertTrue(len(elem) > 0, "This tag should be on the page.")
            self.assertTrue(len(elem) == 1, "This tag has a duplicated name.")
            self.assertTrue(elem[0].get("title"), "Element should have tooltip.")
            if tag.definition:
                self.assertEqual(elem[0].get("title"), tag.definition)
            else:
                self.assertEqual(elem[0].get("title"), "No definition")

    def test_link_to_puc(self):

        response = self.client.get(f"/product/1862/")
        self.assertIn(b"/puc/185", response.content)

    def test_add_puc(self):
        p = Product.objects.get(pk=1864)
        response = self.client.get(f"/product/{p.pk}/").content.decode("utf8")
        response_html = html.fromstring(response)

        self.assertTrue(p.uber_puc == None, "Product should not have an assigned PUC")

        self.assertIn(
            "Assign PUC",
            response_html.xpath('string(//*[@id="button_assign_puc"]/text())'),
            "There should be an Assign PUC button for this product",
        )

        response = self.client.get(f"/product_puc/{p.pk}/")

        self.assertNotContains(
            response,
            "Currently assigned PUC:",
            msg_prefix="Assigned PUC should not be visible",
        )
        # Assign a PUC
        puc = PUC.objects.first()
        self.client.post(f"/product_puc/{p.pk}/", {"puc": f"{puc.id}"})

        response = self.client.get(f"/product_puc/{p.pk}/?").content.decode("utf8")
        self.assertIn(
            "Currently assigned PUC:", response, "Assigned PUC should be visible"
        )

        # PUC is assigned....check that an edit will updated the record
        self.assertTrue(
            ProductToPUC.objects.filter(puc_id=puc.id, product_id=p.pk).exists(),
            "PUC link should exist in table",
        )

        # Assign a new PUC, check that it replaces the old one
        newpuc = PUC.objects.all()[2]
        self.client.post(f"/product_puc/{p.pk}/", {"puc": f"{newpuc.id}"})
        self.assertTrue(
            ProductToPUC.objects.filter(product=p).filter(puc_id=newpuc.id).exists(),
            "PUC link should be updated in table",
        )
        p.refresh_from_db()
        self.assertTrue(p.uber_puc != None, "Product should now have an assigned PUC")

        response = self.client.get(f"/product/{p.pk}/")
        self.assertTrue(response.status_code == 200)
        response_html = html.fromstring(response.content.decode("utf8"))

        self.assertNotIn(
            "Assign PUC",
            response_html.xpath('string(//*[@id="button_assign_puc"]/text())'),
            "There should not be an Assign PUC button for this product",
        )

    def test_document_table_order(self):
        p = Product.objects.get(pk=1850)
        one = p.datadocument_set.all()[0]
        two = p.datadocument_set.all()[1]
        self.assertTrue(
            one.created_at < two.created_at,
            f"Doc |{one.pk}| needs to have been created first",
        )
        t1 = one.title
        t2 = two.title
        response = self.client.get("/product/1850/")
        # see that the more recent document is on the top of the table based
        # on the index of where the title falls in the output
        older_doc_index = response.content.decode("utf8").index(t1)
        newer_doc_index = response.content.decode("utf8").index(t2)
        self.assertTrue(
            older_doc_index > newer_doc_index,
            ("Most recent doc" " should be on top of the table!"),
        )

    def test_puc_not_specified(self):
        """Product 1840 is associated with a PUC that has no prod_fam or
        prod_type specified.
        """
        response = self.client.get("/product/1842/")
        count = response.content.decode("utf-8").count("not specified")
        self.assertEqual(
            count, 2, ("Both prod_fam and prod_type should" "not be specified.")
        )

    def _get_icon_span(self, html, doc_id):
        doc = DataDocument.objects.get(pk=doc_id)
        return html.xpath(f"//a[contains(@href, '{doc.file.url}')]/span")[0].values()[0]

    def test_icons(self):
        response = self.client.get("/product/1872/")
        response_html = html.fromstring(response.content.decode("utf8"))
        icon_span = self._get_icon_span(response_html, 173396)
        self.assertEqual("fa fa-fs fa-file-word", icon_span)
        icon_span = self._get_icon_span(response_html, 173824)
        self.assertEqual("fa fa-fs fa-file-image", icon_span)
        icon_span = self._get_icon_span(response_html, 174238)
        self.assertEqual("fa fa-fs fa-file-word", icon_span)
        icon_span = self._get_icon_span(response_html, 176163)
        self.assertEqual("fa fa-fs fa-file", icon_span)
        icon_span = self._get_icon_span(response_html, 176257)
        self.assertEqual("fa fa-fs fa-file-image", icon_span)
        icon_span = self._get_icon_span(response_html, 177774)
        self.assertEqual("fa fa-fs fa-file-excel", icon_span)
        icon_span = self._get_icon_span(response_html, 177852)
        self.assertEqual("fa fa-fs fa-file-csv", icon_span)
        icon_span = self._get_icon_span(response_html, 178456)
        self.assertEqual("fa fa-fs fa-file-excel", icon_span)
        icon_span = self._get_icon_span(response_html, 178496)
        self.assertEqual("fa fa-fs fa-file-alt", icon_span)
        icon_span = self._get_icon_span(response_html, 172462)
        self.assertEqual("fa fa-fs fa-file-pdf", icon_span)

    def test_puc_kind_field_displayed(self):
        response = self.client.get("/product/11/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<dt>PUC Kind:</dt>")
        self.assertContains(response, Product.objects.get(pk=11).uber_puc.kind)


@override_settings(ALLOWED_HOSTS=["testserver"])
class TestProductImage(TransactionTestCase):
    fixtures = fixtures_standard

    def setUp(self):
        self.client.login(username="Karyn", password="specialP@55word")

    def test_image_upload(self):
        product_pk = 878
        product = Product.objects.get(pk=product_pk)
        post_uri = reverse("product_delete", args=[product_pk])

        product.image.save(
            name="dave_or_grant.png",
            content=open(
                "sample_files/images/products/product_image_upload_valid/dave_or_grant.png",
                "rb",
            ),
            save=True,
        )

        sample_file = open(
            "sample_files/images/products/product_image_upload_valid/dave_or_grant.png",
            "rb",
        )
        saved_image = product.image.open(mode="rb")

        # Verify binary data is identical
        self.assertEqual(saved_image.read(), sample_file.read())

        sample_file.close()
        saved_image.close()

        image_path = product.image.path

        self.assertTrue(
            os.path.exists(image_path), "the stored file should be in MEDIA_ROOT"
        )

        # Delete the product
        self.client.post(post_uri)

        self.assertFalse(
            os.path.exists(image_path),
            "the stored file should no longer be in MEDIA_ROOT",
        )
