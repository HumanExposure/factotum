from lxml import html
from django.test import TestCase, override_settings
from dashboard.models import Product, ProductToPUC
from dashboard.tests.loader import fixtures_standard
from django.core.exceptions import ObjectDoesNotExist


@override_settings(ALLOWED_HOSTS=["testserver"])
class TestProductDetail(TestCase):
    fixtures = fixtures_standard

    def setUp(self):
        self.client.login(username="Karyn", password="specialP@55word")

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
            },
        )
        p.refresh_from_db()
        self.assertEqual(p.title, "x", 'Product 11 should have the title "x"')

    def test_hover_definition(self):
        p = Product.objects.get(pk=11)
        response = self.client.get(f"/product/{str(p.pk)}/")
        lxml = html.fromstring(response.content.decode("utf8"))
        for tag in p.get_puc_tags():
            elem = lxml.xpath(f'//li[@data-tag-name="{tag.name}"]')
            if not elem:
                elem = lxml.xpath(f'//button[@data-tag-name="{tag.name}"]')
            self.assertTrue(len(elem) > 0, "This tag should be on the page.")
            self.assertTrue(len(elem) == 1, "This tag has a duplicated name.")
            if tag.definition:
                self.assertEqual(elem[0].get("title"), tag.definition)
            else:
                self.assertEqual(elem[0].get("title"), "No definition")

    def test_link_to_puc(self):
        response = self.client.get(f"/product/1862/")
        self.assertIn(b"/puc/185", response.content)

    def test_add_puc(self):
        p = Product.objects.get(pk=14)
        response = self.client.get(f"/product/{str(p.pk)}/").content.decode("utf8")
        response_html = html.fromstring(response)

        self.assertTrue(
            p.get_uber_puc() == None, "Product should not have an assigned PUC"
        )

        self.assertIn(
            "Assign PUC",
            response_html.xpath('string(//*[@id="button_assign_puc"]/text())'),
            "There should be an Assign PUC button for this product",
        )

        response = self.client.get(f"/product_puc/{str(p.pk)}/").content.decode("utf8")

        self.assertNotIn(
            "Currently assigned PUC:", response, "Assigned PUC should not be visible"
        )
        # Assign PUC 96
        self.client.post(f"/product_puc/{str(p.pk)}/", {"puc": "96"})

        response = self.client.get(f"/product_puc/{str(p.pk)}/?").content.decode("utf8")
        self.assertIn(
            "Currently assigned PUC:", response, "Assigned PUC should be visible"
        )

        # PUC is assigned....check that an edit will updated the record
        self.assertTrue(
            ProductToPUC.objects.filter(puc_id=96, product_id=p.pk).exists(),
            "PUC link should exist in table",
        )

        # Assign PUC 47, check that it replaces 96
        self.client.post(f"/product_puc/{str(p.pk)}/", {"puc": "47"})
        self.assertTrue(
            ProductToPUC.objects.filter(product=p).filter(puc_id=47).exists(),
            "PUC link should be updated in table",
        )
        p.refresh_from_db()
        self.assertTrue(
            p.get_uber_puc() != None, "Product should now have an assigned PUC"
        )

        response = self.client.get("/product/{str(p.pk)}/").content.decode("utf8")
        response_html = html.fromstring(response)

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
        response = self.client.get("/product/1840/")
        count = response.content.decode("utf-8").count("not specified")
        self.assertEqual(
            count, 2, ("Both prod_fam and prod_type should" "not be specified.")
        )

    def _get_icon_span(self, html, doc):
        return html.xpath("//a[contains(@href, '%s')]/span" % doc)[0].values()[0]

    def test_icons(self):
        response = self.client.get("/product/1872/")
        response_html = html.fromstring(response.content.decode("utf8"))
        icon_span = self._get_icon_span(response_html, "173396.doc")
        self.assertEqual("fa fa-fs fa-file-word", icon_span)
        icon_span = self._get_icon_span(response_html, "173824.jpg")
        self.assertEqual("fa fa-fs fa-file-image", icon_span)
        icon_span = self._get_icon_span(response_html, "174238.docx")
        self.assertEqual("fa fa-fs fa-file-word", icon_span)
        icon_span = self._get_icon_span(response_html, "176163.misc")
        self.assertEqual("fa fa-fs fa-file", icon_span)
        icon_span = self._get_icon_span(response_html, "176257.tiff")
        self.assertEqual("fa fa-fs fa-file-image", icon_span)
        icon_span = self._get_icon_span(response_html, "177774.xlsx")
        self.assertEqual("fa fa-fs fa-file-excel", icon_span)
        icon_span = self._get_icon_span(response_html, "177852.csv")
        self.assertEqual("fa fa-fs fa-file-csv", icon_span)
        icon_span = self._get_icon_span(response_html, "178456.xls")
        self.assertEqual("fa fa-fs fa-file-excel", icon_span)
        icon_span = self._get_icon_span(response_html, "178496.txt")
        self.assertEqual("fa fa-fs fa-file-alt", icon_span)
        icon_span = self._get_icon_span(response_html, "172462.pdf")
        self.assertEqual("fa fa-fs fa-file-pdf", icon_span)
