import json

from django.test import TestCase, override_settings
from dashboard.tests.loader import fixtures_standard
from dashboard.models import Product


@override_settings(ALLOWED_HOSTS=["testserver"])
class TestAjax(TestCase):
    fixtures = fixtures_standard

    @classmethod
    def setUpTestData(cls):
        cls.all_product_count = Product.objects.all().count()

    def test_anonymous_read(self):
        response = self.client.get("/products/")
        self.assertEqual(response.status_code, 200)

    def test_default_params(self):
        response = self.client.get("/p_json/")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEquals(data["recordsTotal"], self.all_product_count)
        self.assertEquals(data["recordsFiltered"], self.all_product_count)
        self.assertEquals(len(data["data"]), 10)

    def test_paging(self):
        response = self.client.get("/p_json/?start=10&length=10")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEquals(data["recordsTotal"], self.all_product_count)
        self.assertEquals(data["recordsFiltered"], self.all_product_count)

        self.assertEquals(len(data["data"]), 10)

    def test_product_search(self):
        response = self.client.get("/p_json/?search[value]=test")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEquals(data["recordsTotal"], self.all_product_count)

        self.assertEquals(data["recordsFiltered"], 1)
        self.assertEquals(len(data["data"]), 1)

    def test_document_search(self):
        response = self.client.get("/d_json/?search[value]=shampoo")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEquals(data["recordsTotal"], 557)
        self.assertEquals(data["recordsFiltered"], 7)
        self.assertEquals(len(data["data"]), 7)

    def test_chemical_search(self):
        response = self.client.get("/c_json/?search[value]=ethylparaben")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEquals(data["recordsTotal"], 8)
        self.assertEquals(data["recordsFiltered"], 1)
        self.assertEquals(len(data["data"]), 1)

    def test_chemicals_by_puc(self):
        response = self.client.get("/c_json/?puc=185")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEquals(data["recordsTotal"], 1)
        self.assertEquals(data["recordsFiltered"], 1)
        self.assertEquals(data["data"][0][0], "DTXSID9022528")

    def test_documents_by_sid(self):
        response = self.client.get("/d_json/?sid=DTXSID9022528")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEquals(data["recordsTotal"], 2)
        self.assertEquals(data["recordsFiltered"], 2)
        self.assertEquals(
            data["data"][1][0],
            "The Healing Garden Rose Whipped Body Lotion Re... / (Ascendia Brands Co., Inc)",
        )

    def test_sids_per_grouptype_combo(self):
        response = self.client.get("/sid_gt_json")
        self.assertEqual(response.status_code, 200)
        payload = json.loads(response.content)
        expected_payload = {
            "data": [
                {"sets": ["Composition"], "size": 7},
                {"sets": ["Composition", "Chemical presence list"], "size": 1},
                {"sets": ["Chemical presence list"], "size": 1},
                {"sets": ["HHE Report"], "size": 2},
                {"sets": ["Composition", "HHE Report"], "size": 1},
            ]
        }
        self.assertEqual(payload, expected_payload)
