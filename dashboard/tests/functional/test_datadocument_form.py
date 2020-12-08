from django.test import RequestFactory, TestCase, override_settings

from dashboard.tests.loader import *
from dashboard.tests.mixins import DashboardFormFieldTestMixin
from dashboard.forms import DataDocumentForm


@override_settings(ALLOWED_HOSTS=["testserver"])
class DataDocumentDetailFormTest(TestCase, DashboardFormFieldTestMixin):
    fixtures = fixtures_standard
    form = DataDocumentForm

    def setUp(self):
        self.factory = RequestFactory()
        self.client.login(username="Karyn", password="specialP@55word")

    def test_field_exclusive_existence(self):
        self.fields_exclusive(
            [
                "title",
                "subtitle",
                "document_type",
                "note",
                "url",
                "raw_category",
                "organization",
                "epa_reg_number",
                "pmid",
            ]
        )

    def test_post_fields(self):
        self.post_field("/datadocument/edit/", "title", "lol", pk=354784)
        self.post_field("/datadocument/edit/", "subtitle", "lol", pk=354784)
        self.post_field("/datadocument/edit/", "document_type", 5, pk=5)
        self.post_field("/datadocument/edit/", "note", "lol", pk=354784)
        self.post_field("/datadocument/edit/", "url", "http://www.epa.gov", pk=8)
        self.post_field("/datadocument/edit/", "raw_category", "raw category", pk=8)
        self.post_field("/datadocument/edit/", "organization", "organization", pk=53)

        # PMID should exist for a document belong to datagroup type LM
        self.post_field("/datadocument/edit/", "pmid", "12345678901234567890", pk=53)

        # PMID should not exist for a document belong to datagroup type HE
        with self.assertRaises(AssertionError):
            self.post_field(
                "/datadocument/edit/", "pmid", "12345678901234567890", pk=354784
            )
