from django.urls import resolve
from django.test import TestCase, tag
from django.test.client import Client
from dashboard.tests.loader import load_model_objects
from dashboard import views
from lxml import html


@tag("loader")
class NavBarTest(TestCase):
    """this group of tests checks to see that the URL resolves to the
    appropriate view function.
    """

    def setUp(self):
        self.objects = load_model_objects()
        self.client = Client()

    def test_home_page_returns_correct_html(self):
        # we need Karyn in the DB in order to log her in.
        # load_model_objects returns a `dot_notation` dict which we can
        # use all of the model objects from, seen in the print stmnt below.
        self.client.login(username="Karyn", password="specialP@55word")
        response = self.client.get("/")
        html = response.content.decode("utf8").rstrip()
        self.assertTrue(html.startswith("<!DOCTYPE html>"))
        self.assertIn("<title>factotum</title>", html)
        self.assertTrue(html.endswith("</html>"))

    def test_index_link(self):
        found = resolve("/")
        self.assertEqual(found.func, views.index)

    def test_data_sources_link(self):
        found = resolve("/datasources/")
        self.assertEqual(found.func, views.data_source_list)

    def test_qa_link(self):
        found = resolve("/qa/compextractionscript/")
        self.assertEqual(found.func, views.qa_extractionscript_index)

    def test_get_data_without_auth(self):
        # the Get Data menu item should be available to a user who isn't logged in
        response = self.client.get("/")
        self.assertContains(response, "Get Data")
        response = self.client.get("/get_data/")
        self.assertContains(response, "Summary Metrics by Chemical")

    def test_data_curation(self):
        self.client.login(username="Karyn", password="specialP@55word")
        response = self.client.get("/").content.decode("utf8")
        response_html = html.fromstring(response)
        self.assertIn(
            "Data Curation",
            response_html.xpath(
                'string(//*[@id="navbarDataCurationDropdownMenuLink"]/text())'
            ),
            "The Data Curation dropdown should appear in the navbar.",
        )

    def test_delete_extractedtext_link(self):
        self.client.login(username="Karyn", password="specialP@55word")
        response = self.client.get("/")
        self.assertContains(response, 'href="/extractionscripts/delete/"')
