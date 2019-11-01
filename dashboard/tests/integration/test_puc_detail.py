from dashboard.tests.loader import fixtures_standard, load_browser
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from dashboard.models import PUC

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
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


class TestPUCProductTable(StaticLiveServerTestCase):
    fixtures = fixtures_standard

    def setUp(self):
        self.browser = load_browser()
        log_karyn_in(self)

    def tearDown(self):
        self.browser.quit()

    def test_puc_product_datatable(self):
        puc = PUC.objects.get(pk=185)
        wait = WebDriverWait(self.browser, 10)
        self.browser.get(self.live_server_url + puc.url)
        input_el = self.browser.find_element_by_xpath(
            '//*[@id="products_filter"]/descendant::input[1]'
        )
        input_el.send_keys("Calgon\n")
        wait.until(
            ec.text_to_be_present_in_element(
                (By.XPATH, "//*[@id='products_info']"),
                "Showing 1 to 1 of 1 entries (filtered from 3 total entries)",
            )
        )
        self.assertInHTML(
            "Showing 1 to 1 of 1 entries (filtered from 3 total entries)",
            self.browser.find_element_by_xpath("//*[@id='products_info']").text,
        )
