from dashboard.tests.loader import fixtures_standard, load_browser
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from dashboard.models import ExtractedText, Script
from selenium.common.exceptions import NoSuchElementException


def log_karyn_in(object):
    """
    Log user in for further testing.
    """
    object.browser.get(object.live_server_url + "/login/")
    body = object.browser.find_element_by_tag_name("body")
    object.assertIn("Please sign in", body.text)
    username_input = object.browser.find_element_by_name("username")
    username_input.send_keys("Karyn")
    password_input = object.browser.find_element_by_name("password")
    password_input.send_keys("specialP@55word")
    object.browser.find_element_by_class_name("btn").click()


class TestEditsWithSeedData(StaticLiveServerTestCase):
    fixtures = fixtures_standard

    def setUp(self):
        self.browser = load_browser()
        log_karyn_in(self)

    def tearDown(self):
        self.browser.quit()

    def test_extracted_text_delete_confirmation(self):
        extraction_script = Script.objects.get(pk=5)
        self.assertEqual(
            2, ExtractedText.objects.filter(extraction_script=extraction_script).count()
        )

        qa_url = self.live_server_url + f"/extractionscripts/delete"
        self.browser.get(qa_url)

        self.assertEqual(
            2, ExtractedText.objects.filter(extraction_script=extraction_script).count()
        )
        with self.assertRaises(NoSuchElementException):
            self.browser.find_element_by_class_name("popover")

        et_delete_button = self.browser.find_element_by_id("et-delete-button-5")
        et_delete_button.send_keys("\n")

        popover_div = self.browser.find_element_by_class_name("popover")
        self.assertIn(
            "This action will delete 2 extracted text records.", popover_div.text
        )

        confirm_button = popover_div.find_element_by_class_name("btn-primary")
        confirm_button.send_keys("\n")

        with self.assertRaises(NoSuchElementException):
            self.browser.find_element_by_id("et-delete-button-5")

        extraction_script.refresh_from_db()
        self.assertEqual(
            0, ExtractedText.objects.filter(extraction_script=extraction_script).count()
        )
        self.assertEqual(False, extraction_script.qa_begun)

    def test_skip_button(self):
        # A Composition page should include a Skip button
        qa_url = self.live_server_url + f"/qa/extractedtext/121698/"
        self.browser.get(qa_url)
        btn_skip = self.browser.find_element_by_name("skip")
        self.assertEqual(btn_skip.text, "Skip")

        # A Chemical Presence page should not
        qa_url = self.live_server_url + f"/qa/extractedtext/254780/"
        self.browser.get(qa_url)
        with self.assertRaises(NoSuchElementException):
            self.browser.find_element_by_name("skip")

