from django.test import TestCase, tag
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError, ObjectDoesNotExist


from dashboard.tests.loader import load_model_objects, fixtures_standard
from dashboard.models import ExtractedText, QANotes


@tag("loader")
class ExtractedTest(TestCase):
    def setUp(self):
        self.objects = load_model_objects()

    def test_extracted_doc_date_validation(self):
        # check validation for proper length string
        text = ExtractedText(
            doc_date="Wednesday, January 21, 2014",
            data_document=self.objects.doc,
            extraction_script=self.objects.script,
        )
        self.assertRaises(ValidationError, text.clean_fields)
        # check validation not thrown for arbitrary date string less than 25 chars
        text = ExtractedText(
            doc_date="January 1984",
            data_document=self.objects.doc,
            extraction_script=self.objects.script,
        )
        try:
            text.clean()
        except ValidationError:
            self.fail("clean() raised ExceptionType unexpectedly!")

        # check validation not thrown if doc_date is null
        text = ExtractedText(
            data_document=self.objects.doc, extraction_script=self.objects.script
        )
        try:
            text.clean()
        except ValidationError:
            self.fail("clean() raised ExceptionType unexpectedly!")

    def test_long_qa_notes(self):
        self.objects.extext.qa_edited = True
        note = QANotes.objects.create(extracted_text=self.objects.extext)
        self.assertEqual(note.qa_notes, None)
        note.qa_notes = "A short QA note"
        try:
            note.clean()
        except Exception as ex:
            template = "An exception of type {0} occurred. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)

        long_note = "A long QA note" * 200
        note.qa_notes = long_note
        try:
            note.clean()
        except Exception as ex:
            template = "An exception of type {0} occurred. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)


class ExtractedTestWithSeedData(TestCase):

    fixtures = fixtures_standard

    def test_approvable(self):
        for et in ExtractedText.objects.filter(qa_edited=False):
            self.assertTrue(et.is_approvable(), "The record should be approvable")
            # Turn it into an edited record
            et.qa_edited = True
            et.save()

            self.assertFalse(
                et.is_approvable(), "Now the record should not be approvable"
            )
            qa = QANotes.objects.create(
                extracted_text=et, qa_notes="Some notes have been added"
            )

            self.assertTrue(
                et.is_approvable(),
                "The record should be approvable after adding a note",
            )
            # Make the qa_notes field blank
            qa.qa_notes = ""
            qa.save()
            self.assertFalse(
                et.is_approvable(),
                "The record should not be approvable if the notes exist but are blank",
            )
