from django.test import TestCase, tag
from django.utils import timezone
from django.contrib.auth.models import User
from dashboard.tests.loader import load_model_objects
from dashboard.models import *


@tag("loader")
class HHTest(TestCase):
    def setUp(self):
        self.objects = load_model_objects()

    def test_hhdoc_creation(self):
        hhds = DataSource.objects.create(
            title="HH Data Source for Test",
            estimated_records=2,
            state="AT",
            priority="HI",
        )
        hhgt = GroupType.objects.get(code="HH")
        hhdlscript = Script.objects.create(
            title="Dummy HHE Download Script",
            url="http://www.epa.gov/",
            qa_begun=False,
            script_type="DL",
        )
        hhexscript = Script.objects.create(
            title="Dummy Extraction Script",
            url="http://www.epa.gov/",
            qa_begun=False,
            script_type="EX",
        )

        hhdg = DataGroup.objects.create(
            name="HH Data Group for Test",
            description="Testing...",
            data_source=hhds,
            download_script=hhdlscript,
            downloaded_by=self.objects.user,
            downloaded_at=timezone.now(),
            group_type=hhgt,
            url="https://www.epa.gov",
        )
        hhdt = DocumentType.objects.get(title="HHE Report", code="HH")

        hhdd = DataDocument.objects.create(
            title="test HHE document",
            data_group=hhdg,
            document_type=hhdt,
            filename="HHexample.pdf",
        )

        exhhdoc = ExtractedHHDoc.objects.create(
            hhe_report_number="2017-0006-3319",
            data_document=hhdd,
            extraction_script=hhexscript,
        )

        self.assertEqual(exhhdoc.__str__(), str(hhdd))

        # Add extracted records to the document
        hhrec1 = ExtractedHHRec.objects.create(
            extracted_text=exhhdoc,
            media="Air",
            sampling_method="1.4 liter evacuated canisters, analytical_method: EPA method TO-15",
            raw_chem_name="carbon disulfide",
        )
        hhrec2 = ExtractedHHRec.objects.create(
            extracted_text=exhhdoc,
            media="Air",
            sampling_method="1.4 liter evacuated canisters, analytical_method: EPA method TO-15",
            raw_chem_name="chloromethane",
        )

        # Test fetching all the records for a given report number
        hhdocs = ExtractedHHDoc.objects.filter(hhe_report_number="2017-0006-3319")
        hhrecs = ExtractedHHRec.objects.filter(extracted_text__in=hhdocs)
        self.assertTrue(
            hhrec1 in hhrecs, "The fetched queryset should contain one of the HHRecs"
        )

        # The same records should be retrievable from the RawChem model by the report number
        rcs = RawChem.objects.select_subclasses().filter(
            extracted_text__in=ExtractedHHDoc.objects.filter(
                hhe_report_number="2017-0006-3319"
            )
        )
        self.assertTrue(
            hhrec1 in rcs, "The fetched queryset should contain one of the HHRecs"
        )
