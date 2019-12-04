import json

from django.test import TestCase, override_settings
from dashboard.tests.loader import fixtures_standard


@override_settings(ALLOWED_HOSTS=["testserver"])
class TestProductList(TestCase):
    fixtures = fixtures_standard

    def test_anonymous_read(self):
        response = self.client.get("/products/")
        self.assertEqual(response.status_code, 200)

    def test_default_params(self):
        response = self.client.get("/p_json/")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEquals(data["recordsTotal"], 35)
        self.assertEquals(data["recordsFiltered"], 35)
        self.assertEquals(len(data["data"]), 10)

    def test_paging(self):
        response = self.client.get("/p_json/?start=10&length=10")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEquals(data["recordsTotal"], 35)
        self.assertEquals(data["recordsFiltered"], 35)
        self.assertEquals(len(data["data"]), 10)

    def test_search(self):
        response = self.client.get("/p_json/?search[value]=test")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEquals(data["recordsTotal"], 35)
        self.assertEquals(data["recordsFiltered"], 1)
        self.assertEquals(len(data["data"]), 1)
