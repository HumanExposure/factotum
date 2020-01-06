import json

from django.test import TestCase

from dashboard.models import DSSToxLookup, ProductDocument, PUC, ProductToPUC
from dashboard.tests.loader import fixtures_standard


class ChemicalDetail(TestCase):

    fixtures = fixtures_standard

    def setUp(self):
        self.client.login(username="Karyn", password="specialP@55word")

    def test_chemical_detail(self):
        dss = next(dss for dss in DSSToxLookup.objects.all() if dss.puc_count > 0)
        response = self.client.get(dss.get_absolute_url())
        self.assertEqual(
            dss.cumulative_puc_count,
            len(response.context["pucs"]),
            f"DSSTox pk={dss.pk} needs {dss.cumulative_puc_count} PUCs in the context",
        )

        pdocs = ProductDocument.objects.from_chemical(dss)
        first_puc_id = (
            PUC.objects.filter(products__in=pdocs.values("product")).first().id
        )

        self.assertContains(response, f'a href="/puc/{first_puc_id}')
        link = "https://comptox.epa.gov/dashboard/dsstoxdb/results?search=" f"{dss.sid}"
        self.assertContains(response, link)
        dss = next(dss for dss in DSSToxLookup.objects.all() if dss.puc_count < 1)
        response = self.client.get(dss.get_absolute_url())
        self.assertEqual(
            dss.cumulative_puc_count,
            len(response.context["pucs"]),
            f"DSSTox pk={dss.pk} needs {dss.cumulative_puc_count} PUCs in the context",
        )
        self.assertContains(response, "No PUCs are linked to this chemical")

        # Confirm that the list is displaying unique PUCs:
        # Set all the Ethylparaben-linked ProductToPuc relationships to a single PUC
        dss = DSSToxLookup.objects.get(sid="DTXSID9022528")
        ep_prods = ProductDocument.objects.from_chemical(dss).values_list("product_id")
        ProductToPUC.objects.filter(product_id__in=ep_prods).update(puc_id=210)

        response = self.client.get(dss.get_absolute_url())
        self.assertEqual(
            dss.cumulative_puc_count,
            len(response.context["pucs"]),
            f"DSSTox pk={dss.pk} should return {dss.cumulative_puc_count} for the tree",
        )

        # Check cumulative product count
        pucs = (
            PUC.objects.dtxsid_filter("DTXSID6026296")
            .with_num_products()
            .filter(gen_cat="Arts and Crafts/Office supplies")
        )
        cumulative_sum = sum(puc.num_products for puc in pucs)
        response_for_water = self.client.get("/chemical/DTXSID6026296/")
        self.assertEqual(
            cumulative_sum,
            response_for_water.context["pucs"].children[0].value.cumnum_products,
            f'Water sid ("DTXSID6026296") should have {cumulative_sum} associated products '
            + f"but returns {response_for_water.context['pucs'].children[0].value.cumnum_products}",
        )

    def _n_children(self, children):
        cnt = sum(1 for c in children if "value" in c)
        for c in children:
            if "children" in c:
                cnt += self._n_children(c["children"])
        return cnt

    def test_puc_bubble_query(self):
        dss = next(dss for dss in DSSToxLookup.objects.all() if dss.puc_count > 0)
        response = self.client.get(f"/dl_pucs_json/?dtxsid={dss.sid}")
        d = json.loads(response.content)
        self.assertEqual(
            dss.puc_count,
            self._n_children(d["children"]),
            f"DSSTox pk={dss.pk} should have {dss.puc_count} PUCs in the JSON",
        )

    def test_cp_keyword_set(self):
        dss = DSSToxLookup.objects.get(sid="DTXSID9020584")
        response = self.client.get(dss.get_absolute_url())
        self.assertEqual(
            len(response.context["keysets"]),
            4,
            f"DSSTox pk={dss.pk} should return 4 CP keyword sets in the context",
        )

        for keyset in response.context["keysets"]:
            self.assertEqual(
                keyset.count,
                1,
                f"DSSTox pk={dss.pk} should keyword sets should all have 1 document associated with them",
            )

    def test_anonymous_read(self):
        self.client.logout()
        response = self.client.get("/chemical/DTXSID6026296/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Water")
