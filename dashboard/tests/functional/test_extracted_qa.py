from django.test import TestCase, tag
from dashboard.tests.loader import load_model_objects
from dashboard.models import QAGroup, ExtractedText


@tag("loader")
class ExtractedQaTest(TestCase):
    def setUp(self):
        self.objects = load_model_objects()
        self.client.login(username="Karyn", password="specialP@55word")

    def test_qa_group_creation(self):
        # test the assignment of a qa_group to extracted text objects
        pk = self.objects.extext.pk
        self.assertIsNone(self.objects.extext.qa_group)
        self.assertEqual(len(QAGroup.objects.all()), 0)
        pk = self.objects.extext.extraction_script.pk
        response = self.client.get(f"/qa/compextractionscript/{pk}/")
        self.assertEqual(response.status_code, 200)
        qa_group = QAGroup.objects.get(
            extraction_script=self.objects.extext.extraction_script
        )
        ext = ExtractedText.objects.get(qa_group=qa_group)
        self.assertIsNotNone(ext.qa_group)
        response = self.client.get(f"/qa/extractedtext/{ext.pk}/")

    def test_qa_approval_redirect(self):
        # first need to create a QAGroup w/ this get request.
        self.client.get(f"/qa/compextractionscript/{self.objects.exscript.pk}/")
        pk = self.objects.extext.pk
        response = self.client.post(f"/extractedtext/approve/{pk}/")
        self.assertEqual(
            response.url,
            "/qa/compextractionscript/",
            (
                "User should be redirected to "
                "QA homepage after last extext is approved."
            ),
        )
