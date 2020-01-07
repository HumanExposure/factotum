from dashboard.tests.loader import fixtures_standard
from django.contrib.auth.models import User
from dashboard import views
from django.test import TestCase, override_settings, RequestFactory
from dashboard.models import (
    RawChem,
    Script,
    ExtractedText,
    QAGroup,
    QANotes,
    ExtractedListPresence,
)
from django.db.models import Count
from lxml import html


@override_settings(ALLOWED_HOSTS=["testserver"])
class TestQaPage(TestCase):
    fixtures = fixtures_standard

    def setUp(self):
        self.factory = RequestFactory()
        self.client.login(username="Karyn", password="specialP@55word")

    def test_qa_begin(self):
        """
        Check that starting the QA process flips the variable on the Script
        """
        self.assertFalse(
            Script.objects.get(pk=5).qa_begun,
            "The Script should have qa_begun of False at the beginning",
        )
        self.client.get("/qa/compextractionscript/5/")
        self.assertTrue(
            Script.objects.get(pk=5).qa_begun, "qa_begun should now be true"
        )

    def test_new_qa_group_urls(self):
        # Begin from the QA index page
        response = self.client.get(f"/qa/compextractionscript/")
        self.assertIn(
            f"/qa/compextractionscript/15/'> Begin QA".encode(), response.content
        )
        # Script 15 has one ExtractedText object
        pk = 15
        response = self.client.get(f"/qa/compextractionscript/{pk}/")
        et = ExtractedText.objects.filter(extraction_script=pk).first()
        self.assertIn(f"/qa/extractedtext/{et.pk}/".encode(), response.content)
        # After opening the URL, the following should be true:
        # One new QA group should be created
        group_count = QAGroup.objects.filter(extraction_script_id=pk).count()
        self.assertTrue(group_count == 1)
        # The ExtractionScript's qa_begun property should be set to True
        self.assertTrue(Script.objects.get(pk=15).qa_begun)
        # The ExtractedText object should be assigned to the QA Group
        group_pk = QAGroup.objects.get(extraction_script_id=pk).pk
        et = ExtractedText.objects.filter(extraction_script=pk).first()
        self.assertTrue(et.qa_group_id == group_pk)
        # The link on the QA index page should now say "Continue QA"
        response = self.client.get(f"/qa/compextractionscript/")
        self.assertIn(
            f"'/qa/compextractionscript/15/'> Continue QA".encode(), response.content
        )

    def test_doc_fields(self):
        """ The subtitle and note field should appear on the page """
        response = self.client.get(f"/qa/extractedtext/254780/")
        self.assertIn("Lorem ipsum dolor".encode(), response.content)
        self.assertIn("A list of chemicals with a subtitle".encode(), response.content)

    def test_qa_script_without_ext_text(self):
        # Begin from the QA index page
        response = self.client.get(f"/qa/compextractionscript/")
        self.assertIn(
            f"/qa/compextractionscript/15/'> Begin QA".encode(), response.content
        )
        # Script 9 has no ExtractedText objects
        pk = 9
        # a user will see no link on the QA index page, but it's still
        # possible to enter the URL
        response = self.client.get(f"/qa/compextractionscript/{pk}/", follow=True)
        self.assertEqual(response.status_code, 200)

    def test_data_document_qa(self):
        # Open the QA page for a Composition ExtractedText record w/ no QA group
        # and is in a Script with < 100 documents
        scr = (
            Script.objects.annotate(num_ets=Count("extractedtext"))
            .filter(num_ets__lt=100)
            .filter(script_type="EX")
            .first()
        )
        pk = (
            ExtractedText.objects.filter(qa_group=None)
            .filter(extraction_script=scr)
            .filter(data_document__data_group__group_type__code="CO")
            .first()
            .pk
        )
        response = self.client.get(f"/qa/extractedtext/{pk}/")

        # After opening the QA link from the data document detail page, the
        # following should be true:
        # One new QA group should be created
        scr = ExtractedText.objects.get(pk=pk).extraction_script
        group_count = QAGroup.objects.filter(extraction_script=scr).count()
        self.assertTrue(group_count == 1)
        # The ExtractionScript's qa_begun property should be set to True
        self.assertTrue(scr.qa_begun)
        # The ExtractedText object should be assigned to the QA Group
        new_group = QAGroup.objects.get(extraction_script=scr)
        et = ExtractedText.objects.get(pk=pk)
        self.assertTrue(et.qa_group == new_group)
        # The link on the QA index page should now say "Continue QA"
        response = self.client.get(f"/qa/compextractionscript/")
        self.assertContains(
            response, f"'/qa/compextractionscript/{scr.pk}/'> Continue QA"
        )

        # Open the QA page for an ExtractedText record that has no QA group and
        # is related to a script with over 100 documents
        scr = (
            Script.objects.annotate(num_ets=Count("extractedtext"))
            .filter(num_ets__gt=100)
            .first()
        )
        pk = ExtractedText.objects.filter(extraction_script=scr).first().pk
        response = self.client.get(f"/qa/extractedtext/{pk}/")
        scr = ExtractedText.objects.get(pk=pk).extraction_script
        # After opening the QA link from the data document detail page, the
        # following should be true:
        # One new QA group should be created
        new_group = QAGroup.objects.get(extraction_script=scr)

        # There should be a lot of ExtractedText records assigned to the QAGroup
        initial_qa_count = ExtractedText.objects.filter(qa_group=new_group).count()
        self.assertTrue(initial_qa_count > 100)

        # Select a document that shares a Script with the
        # QA Group created above BUT DOES NOT BELONG TO THE QA GROUP
        pk = (
            ExtractedText.objects.filter(extraction_script=scr)
            .filter(qa_group=None)
            .first()
        ).pk
        # Open its QA page via the /datdocument/qa path
        response = self.client.get(f"/qa/extractedtext/{pk}/")
        # Make sure that the number of documents in the QA Group has increased
        self.assertGreater(
            ExtractedText.objects.filter(qa_group=new_group).count(), initial_qa_count
        )

    def test_habitsandpractices(self):
        # Begin from the QA index page
        response = self.client.get(f"/habitsandpractices/54/")
        self.assertContains(response, "<b>Add New Habit and Practice</b>")

    def test_dd_link(self):
        # Open the Script page to create a QA Group
        response = self.client.get("/qa/extractedtext/5", follow=True)
        self.assertIn(b"/datadocument/5", response.content)

    def test_approval(self):
        # Open the Script page to create a QA Group
        self.client.get("/qa/compextractionscript/5", follow=True)
        # Follow the first approval link
        self.client.get("/qa/extractedtext/7", follow=True)

    def test_detail_edits(self):
        """
        After editing a detail ("child") record, confirm that
        the save and approval functions work
        """

        resp = self.client.get("/qa/extractedtext/7/")
        # import pdb; pdb.set_trace()
        self.assertContains(resp, 'value="dibutyl_phthalate"', status_code=200)

        post_context = {
            "csrfmiddlewaretoken": [
                "BvtzIX6JjC5XkPWmAOduJllMTMdRLoVWeJtneuBVe5Bc3Js35EVsJunvII6vNFAy"
            ],
            "rawchem-TOTAL_FORMS": ["2"],
            "rawchem-INITIAL_FORMS": ["1"],
            "rawchem-MIN_NUM_FORMS": ["0"],
            "rawchem-MAX_NUM_FORMS": ["1000"],
            "save": [""],
            "rawchem-0-extracted_text": ["7"],
            "rawchem-0-true_cas": ["84-74-2"],
            "rawchem-0-true_chemname": ["dibutyl phthalate"],
            "rawchem-0-SID": ["DTXSID2021781"],
            "rawchem-0-rawchem_ptr": ["4"],
            # change the raw_chem_name
            "rawchem-0-raw_chem_name": ["dibutyl phthalate edited"],
            "rawchem-0-raw_cas": ["84-74-2"],
            "rawchem-0-raw_min_comp": ["4"],
            "rawchem-0-raw_central_comp": [""],
            "rawchem-0-raw_max_comp": ["7"],
            "rawchem-0-unit_type": ["1"],
            "rawchem-0-report_funcuse": ["swell"],
            "rawchem-0-ingredient_rank": [""],
            "rawchem-1-extracted_text": ["7"],
            "rawchem-1-rawchem_ptr": [""],
            "rawchem-1-raw_chem_name": [""],
            "rawchem-1-raw_cas": [""],
            "rawchem-1-raw_min_comp": [""],
            "rawchem-1-raw_central_comp": [""],
            "rawchem-1-raw_max_comp": [""],
            "rawchem-1-unit_type": [""],
            "rawchem-1-report_funcuse": [""],
            "rawchem-1-ingredient_rank": [""],
        }

        request = self.factory.post(path="/qa/extractedtext/7/", data=post_context)

        request.user = User.objects.get(username="Karyn")
        request.session = {}
        request.save = [""]
        resp = views.extracted_text_qa(pk=7, request=request)
        # The response has a 200 status code and contains the
        # new edited value
        self.assertContains(resp, 'value="dibutyl phthalate edited"', status_code=200)

        # Check the ORM objects here to make sure the editing has proceeded
        # correctly and the qa-related attributes are updated
        et = ExtractedText.objects.get(pk=7)
        self.assertEqual(et.qa_edited, True)

        # The RawChem object of interest is the one with the first detail form
        rc_key = post_context["rawchem-0-rawchem_ptr"][0]
        rc = RawChem.objects.get(pk=rc_key)

        # The raw_chem_name matches the new value
        self.assertEqual(rc.raw_chem_name, "dibutyl phthalate edited")
        # The dsstox link has been broken
        self.assertFalse(rc.sid)

        # Change a different value and try to save it
        post_context.update({"rawchem-0-raw_central_comp": "6"})

        request = self.factory.post(path="/qa/extractedtext/7/", data=post_context)
        request.user = User.objects.get(username="Karyn")
        request.session = {}
        request.save = [""]
        resp = views.extracted_text_qa(pk=7, request=request)
        # The second edit appears in the page
        self.assertContains(
            resp, 'name="rawchem-0-raw_central_comp" value="6"', status_code=200
        )

    def test_hidden_fields(self):
        """ExtractionScript 15 includes a functional use data group with pk = 5.
        Its QA page should hide the composition fields """
        # Create the QA group by opening the Script's page
        response = self.client.get("/qa/compextractionscript/15/", follow=True)
        # Open the DataGroup's first QA approval link
        response = self.client.get("/qa/extractedtext/5/", follow=True)
        # A raw_cas field should be in the page
        self.assertIn(b'<input type="text" name="rawchem-1-raw_cas"', response.content)
        # There should not be any unit_type field in the functional use QA display
        self.assertNotIn(
            b'<input type="text" name="rawchem-1-unit_type"', response.content
        )
        # The values shown should match the functional use record, not the chemical record
        self.assertIn(b"Functional Use Chem1", response.content)

        # Go back to a different ExtractionScript
        response = self.client.get("/qa/compextractionscript/5", follow=True)
        # Open the QA page for a non-FunctionalUse document
        response = self.client.get("/qa/extractedtext/7/", follow=True)
        # This page should include a unit_type input form
        self.assertIn(b"rawchem-1-unit_type", response.content)

    def test_cpcat_qa(self):
        # Begin from the Chemical Presence QA index page
        response = self.client.get(f"/qa/chemicalpresence/")
        self.assertIn(
            f"/qa/chemicalpresencegroup/49/'> View Chemical Presence Lists".encode(),
            response.content,
        )

        response = self.client.get(f"/qa/chemicalpresencegroup/49", follow=True)
        # The table should include the "Begin QA" link
        self.assertIn(
            f'/qa/extractedtext/254781/"> Begin QA'.encode(), response.content
        )

        elps = ExtractedListPresence.objects.filter(
            extracted_text__data_document_id=254781
        )
        self.assertEqual(elps.filter(qa_flag=True).count(), 0)
        response = self.client.get(f"/qa/extractedtext/254781/", follow=True)
        # Navigating to the extractedtext QA page should cause
        # the sampled child records to be flagged with qa_flag=True
        elps = ExtractedListPresence.objects.filter(
            extracted_text__data_document_id=254781
        )
        self.assertEqual(elps.filter(qa_flag=True).count(), 30)

        # The QA page should only show the flagged records
        elp_flagged = elps.filter(qa_flag=True).first()
        self.assertIn(elp_flagged.raw_cas.encode(), response.content)

        elp_not_flagged = elps.filter(qa_flag=False).first()
        self.assertNotContains(response, elp_not_flagged.raw_cas)

    def test_every_extractedtext_qa(self):
        # Attempt to open a QA page for every ExtractedText record
        for et in ExtractedText.objects.all():
            response = self.client.get(
                f"/qa/extractedtext/%s" % et.data_document_id, follow=True
            )
            if response.status_code != 200:
                pass

            self.assertEqual(response.status_code, 200)

    def test_qa_summary(self):
        es = Script.objects.get(pk=5)
        extext = ExtractedText.objects.get(pk=7)
        response = self.client.get(
            f"/qa/compextractionscript/{es.pk}/summary"
        ).content.decode("utf8")
        response_html = html.fromstring(response)
        extractedtext_count = response_html.xpath(
            'string(//*[@id="extractedtext_count"])'
        )
        qa_complete_extractedtext_count = response_html.xpath(
            'string(//*[@id="qa_complete_extractedtext_count"])'
        )
        qa_incomplete_extractedtext_count = response_html.xpath(
            'string(//*[@id="qa_incomplete_extractedtext_count"])'
        )
        self.assertEqual(
            extractedtext_count,
            "2",
            "Two total documents should be associated with this script.",
        )
        self.assertEqual(
            qa_complete_extractedtext_count, "0", "0 documents should be approved."
        )
        self.assertEqual(
            qa_incomplete_extractedtext_count, "2", "2 documents should be unapproved."
        )
        qa_note_count = int(response_html.xpath('count(//*[@id="qa_notes"])'))
        self.assertEqual(
            qa_note_count, 0, "There should be no QA Notes associated with this script."
        )

        QANotes.objects.create(extracted_text=extext, qa_notes="Test QA Note")
        extext.qa_checked = True
        extext.save()

        response = self.client.get(
            f"/qa/compextractionscript/{es.pk}/summary"
        ).content.decode("utf8")
        response_html = html.fromstring(response)
        extractedtext_count = response_html.xpath(
            'string(//*[@id="extractedtext_count"])'
        )
        qa_complete_extractedtext_count = response_html.xpath(
            'string(//*[@id="qa_complete_extractedtext_count"])'
        )
        qa_incomplete_extractedtext_count = response_html.xpath(
            'string(//*[@id="qa_incomplete_extractedtext_count"])'
        )
        self.assertEqual(
            extractedtext_count,
            "2",
            "Two total documents should be associated with this script.",
        )
        self.assertEqual(
            qa_complete_extractedtext_count, "1", "1 document should now be approved."
        )
        self.assertEqual(
            qa_incomplete_extractedtext_count, "1", "1 document should be unapproved."
        )
        qa_note_count = int(response_html.xpath('count(//*[@id="qa_notes"])'))
        self.assertEqual(
            qa_note_count, 1, "There should be 1 QA Note associated with this script."
        )
