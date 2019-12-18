from lxml import html

from django.test import TestCase, tag

from dashboard.tests.loader import fixtures_standard
from dashboard.models import Script, ExtractedText, RawChem, DataDocument


@tag("loader")
class QATest(TestCase):
    fixtures = fixtures_standard

    def setUp(self):
        self.client.login(username="Karyn", password="specialP@55word")

    def test_qa_scoreboard(self):
        scripts = Script.objects.filter(script_type="EX").exclude(extractedtext=None)
        response = self.client.get("/qa/compextractionscript/").content.decode("utf8")
        response_html = html.fromstring(response)

        row_count = len(
            response_html.xpath('//table[@id="extraction_script_table"]/tbody/tr')
        )
        self.assertNotEqual(
            scripts.count(), row_count, ("Scripts w/ CP type texts should be excluded.")
        )

        script = scripts.first()
        href = response_html.xpath(f'//*[@id="script-{script.pk}"]/@href')[0]
        self.assertEqual(
            script.url, href, "There should be an external link to the script."
        )
        td = response_html.xpath(f'//*[@id="docs-{script.pk}"]').pop()
        model_doc_count = ExtractedText.objects.filter(extraction_script=script).count()

        self.assertEqual(
            int(td.text),
            model_doc_count,
            (
                "The displayed number of datadocuments should match "
                "the number whose related extracted text objects used"
                " the extraction script"
            ),
        )

        td = response_html.xpath(f'//*[@id="pct-{script.pk}"]').pop()
        self.assertEqual(
            td.text,
            script.get_pct_checked(),
            ("The displayed percentage should match " "what is derived from the model"),
        )
        self.assertEqual(
            script.get_qa_complete_extractedtext_count(),
            0,
            (
                "The ExtractionScript object should return 0 "
                "qa_checked ExtractedText objects"
            ),
        )

        # Set qa_checked property to True for one of the ExtractedText objects
        et = script.extractedtext_set.first()
        self.assertFalse(et.qa_checked)
        et.qa_checked = True
        et.save()
        self.assertEqual(
            script.get_qa_complete_extractedtext_count(),
            1,
            (
                "The ExtractionScript object should now return "
                "1 qa_checked ExtractedText object"
            ),
        )

        # A button for each row that will take you to the script's QA page
        script_qa_link = response_html.xpath(f'//*[@id="qa-{script.pk}"]/a/@href').pop()
        self.assertIn(f"/qa/compextractionscript/{script.pk}/", script_qa_link)

        # Before clicking link, the script's qa_done property should be false
        self.assertFalse(script.qa_begun, "The property should be False")

        # Link should open a page where the h1 text matches title of the Script
        response = self.client.get(script_qa_link)
        response_html = html.fromstring(response.content.decode("utf8"))
        h1 = response_html.xpath(f'//*[@id="script-{script.pk}"]').pop()
        self.assertIn(
            script.title,
            h1.text_content(),
            "The <h1> text should equal the .title of the Script",
        )

        # Opening ExtractionScript QA page should set qa_begun property to True
        script.refresh_from_db()
        self.assertTrue(
            script.qa_begun,
            ("The qa_begun property of the " "ExtractionScript should now be True"),
        )

        # Go back to the QA index page to confirm that the QA is complete
        response = self.client.get("/qa/compextractionscript/").content.decode("utf8")
        response_html = html.fromstring(response)
        status = response_html.xpath(f'//*[@id="qa-{script.pk}"]/a').pop()
        self.assertIn(
            "QA Complete",
            status.text,
            (
                "The QA Status field should now say "
                '"QA Complete" instead of "Begin QA"'
            ),
        )

    def test_component_label(self):
        data_document = DataDocument.objects.get(pk=354787)
        rawchem = RawChem.objects.get(pk=853)
        component = rawchem.component
        response = self.client.get("/qa/extractedtext/%i/" % data_document.pk)
        response_html = html.fromstring(response.content)
        component_text = response_html.xpath(
            f'//*[@id="component-{rawchem.id}"]/text()'
        )
        self.assertIn(component, component_text)
