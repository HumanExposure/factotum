from dashboard.tests.loader import fixtures_standard, load_browser
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By


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


class TestBulkProductPuc(StaticLiveServerTestCase):
    fixtures = fixtures_standard

    def setUp(self):
        self.browser = load_browser()
        log_karyn_in(self)

    def tearDown(self):
        self.browser.quit()

    def test_select_all(self):
        qa_url = self.live_server_url + f"/bulk_product_puc/?q=cream"
        self.browser.get(qa_url)

        select_all_button = self.browser.find_element_by_class_name("select-checkbox")
        select_all_button.click()

        select_puc_dropdown = Select(self.browser.find_element_by_id("id_puc"))
        select_puc_dropdown.select_by_index(1)

        self.browser.find_element_by_id("btn-assign-puc").click()

        # Now all these products previously returned should be associated with a PUC
        self.browser.get(qa_url)
        body = self.browser.find_element_by_tag_name("body")
        self.assertIn(
            'products matching "cream" are already associated with a PUC.', body.text
        )
