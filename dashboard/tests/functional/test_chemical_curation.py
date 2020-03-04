import csv

from django.test import TestCase
from django.urls import resolve

from dashboard.tests.loader import fixtures_standard
from dashboard.models import RawChem, DSSToxLookup, DataDocument, ExtractedChemical
from dashboard.forms import ExtractedFunctionalUseForm, ChemicalCurationFormSet
from ...views import ChemCreateView, ChemUpdateView


class ChemicalCurationTests(TestCase):
    fixtures = fixtures_standard

    def setUp(self):
        self.client.login(username="Karyn", password="specialP@55word")

    def test_chemical_curation_page(self):
        """
        Ensure there is a chemical curation page
        :return: a 200 status code
        """
        response = self.client.get("/chemical_curation/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Download Uncurated Chemicals by Data Group")

        # Pick one curated and one non-curated RawChem record, and
        # confirm that the downloaded file excludes and includes them,
        # respectively.
        rc = RawChem.objects.filter(dsstox_id__isnull=True).first()
        dg = rc.extracted_text.data_document.data_group
        response = self.client.get(f"/dl_raw_chems_dg/{dg.id}", follow=True)
        header = "id,raw_cas,raw_chem_name,rid,datagroup_id\n"

        resp = list(response.streaming_content)
        response_header = resp[0].decode("utf-8")
        self.assertEqual(
            header, response_header.split("\r\n")[0], "header fields should match"
        )

        rc_row = f'{rc.id},{rc.raw_cas},{rc.raw_chem_name},{rc.rid if rc.rid else ""},{rc.data_group_id}'
        self.assertIn(
            bytes(rc_row, "utf-8"),
            b"\t".join(resp),
            "The non-curated row should appear",
        )

        rc = RawChem.objects.filter(dsstox_id__isnull=False).first()
        dg = rc.extracted_text.data_document.data_group
        response = self.client.get(f"/dl_raw_chems_dg/{dg.id}/", follow=True)
        self.assertTrue(response.status_code == 200)
        resp = list(response.streaming_content)
        rc = RawChem.objects.filter(dsstox_id__isnull=False).first()
        rc_row = f'{rc.id},{rc.raw_cas},{rc.raw_chem_name},{rc.rid if rc.rid else ""},{rc.data_group_id}'
        self.assertNotIn(
            bytes(rc_row, "utf-8"),
            b"\t".join(resp),
            "The curated row should not appear",
        )

    def test_chemical_curation_upload(self):
        # Load data from csv
        with open("./sample_files/chemical_curation_upload.csv") as csv_file:
            reader = csv.DictReader(csv_file)
            rows = [row for row in reader]
        self.assertIsNotNone(rows, "CSV failed to read")

        with open("./sample_files/chemical_curation_upload.csv") as csv_file:
            self.client.post(
                "/chemical_curation/", {"curate-bulkformsetfileupload": csv_file}
            )

        for row in rows:
            # All true chemicals in the CSV should exist
            self.assertEqual(
                1,
                DSSToxLookup.objects.filter(sid=row["sid"]).count(),
                "A matching sid should exist",
            )
            rawchem = RawChem.objects.select_related("dsstox").get(
                pk=row["external_id"]
            )
            # All Raw Chemicals in the CSV should be associated
            self.assertIsNotNone(
                rawchem.dsstox,
                f"RawChem {rawchem.pk} was not associated with any DSSTOX",
            )
            # All Raw Chemicals in the CSV should be associated with the correct sid
            self.assertEqual(
                rawchem.dsstox.sid,
                row["sid"],
                f"RawChem {rawchem.pk} was not associated with {row['sid']}",
            )

    def test_chem_create_url_resolves_view(self):
        doc = DataDocument.objects.first()
        view = resolve(f"/chemical/{doc.pk}/create/")
        self.assertEquals(view.func.view_class, ChemCreateView)

    def test_chem_update_url_resolves_view(self):
        chem = ExtractedChemical.objects.first()
        view = resolve(f"/chemical/{chem.pk}/edit/")
        self.assertEquals(view.func.view_class, ChemUpdateView)

    def test_chemical_create_and_edit(self):
        doc = DataDocument.objects.filter(
            extractedtext__isnull=False, data_group__group_type__code="CP"
        ).first()
        initial_chem_count = doc.extractedtext.rawchem.count()
        data = {"raw_chem_name": "New Name", "raw_cas": "New Raw CAS"}
        mng_data = {
            "functional_uses-TOTAL_FORMS": "0",
            "functional_uses-INITIAL_FORMS": "0",
            "functional_uses-MIN_NUM_FORMS": "",
            "functional_uses-MAX_NUM_FORMS": "",
        }
        data.update(mng_data)
        response = self.client.post(f"/chemical/{doc.pk}/create/", data)
        self.assertEqual(doc.extractedtext.rawchem.count(), initial_chem_count + 1)
        qs = doc.extractedtext.rawchem.filter(raw_chem_name="New Name")
        self.assertTrue(qs.count() == 1)
        chem = doc.extractedtext.rawchem.select_subclasses().first()
        response = self.client.post(f"/chemical/{chem.pk}/edit/", data)
        qs = doc.extractedtext.rawchem.filter(raw_chem_name="New Name")
        self.assertTrue(qs.count() == 2)

    def test_chemical_curation_formset(self):

        with open("./sample_files/chemical_curation_header.csv") as csv_file:
            response = self.client.post(
                "/chemical_curation/", {"curate-bulkformsetfileupload": csv_file}
            )
        self.assertContains(
            response,
            "CSV column titles should be "
            "[&#39;external_id&#39;, &#39;rid&#39;, &#39;sid&#39;, "
            "&#39;true_chemical_name&#39;, &#39;true_cas&#39;]",
        )

        with open("./sample_files/chemical_curation_no_rawchem.csv") as csv_file:
            response = self.client.post(
                "/chemical_curation/", {"curate-bulkformsetfileupload": csv_file}
            )
        self.assertContains(
            response,
            "external_id: Select a valid choice. "
            "That choice is not one of the available choices. (row 1)",
        )

        with open("./sample_files/chemical_curation_bad_sid.csv") as csv_file:
            response = self.client.post(
                "/chemical_curation/", {"curate-bulkformsetfileupload": csv_file}
            )
        self.assertContains(
            response,
            "sid: DDXSID0029501 does not begin with &quot;DTXSID&quot; (row 1)",
        )
        self.assertContains(
            response, "sid: DTXSID204 4769 cannot have a blank character (row 12)"
        )

        with open("./sample_files/chemical_curation_bad_cas.csv") as csv_file:
            response = self.client.post(
                "/chemical_curation/", {"curate-bulkformsetfileupload": csv_file}
            )
        self.assertContains(
            response,
            "true_cas: Ensure this value has at most 50 characters (it has 111)",
        )
