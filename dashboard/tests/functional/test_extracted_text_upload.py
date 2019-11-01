import io

from django.test import RequestFactory, TestCase, Client
from django.contrib.auth.models import User
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware

from dashboard import views
from dashboard.models import (
    ExtractedText,
    DataDocument,
    DataGroup,
    ExtractedChemical,
    ExtractedCPCat,
    ExtractedListPresence,
    ExtractedFunctionalUse,
    RawChem,
)


def make_upload_csv(filename):
    with open(filename) as f:
        sample_csv = "".join([line for line in f.readlines()])
    sample_csv_bytes = sample_csv.encode(encoding="UTF-8", errors="strict")
    in_mem_sample_csv = InMemoryUploadedFile(
        file=io.BytesIO(sample_csv_bytes),
        field_name="extfile-bulkformsetfileupload",
        name="test.csv",
        content_type="text/csv",
        size=len(sample_csv),
        charset="utf-8",
    )
    return in_mem_sample_csv


class UploadExtractedFileTest(TestCase):
    fixtures = [
        "00_superuser.yaml",
        "01_lookups.yaml",
        "02_datasource.yaml",
        "03_datagroup.yaml",
        "04_PUC.yaml",
        "05_product.yaml",
        "06_datadocument.yaml",
        "08_script.yaml",
    ]

    def setUp(self):
        self.mng_data = {
            "extfile-TOTAL_FORMS": "0",
            "extfile-INITIAL_FORMS": "0",
            "extfile-MAX_NUM_FORMS": "",
        }
        self.c = Client()
        self.factory = RequestFactory()
        self.c.login(username="Karyn", password="specialP@55word")

    def generate_valid_chem_csv(self):
        csv_string = (
            "data_document_id,data_document_filename,"
            "prod_name,doc_date,rev_num,raw_category,raw_cas,raw_chem_name,"
            "report_funcuse,raw_min_comp,raw_max_comp,unit_type,"
            "ingredient_rank,raw_central_comp,component"
            "\n"
            "8,11177849.pdf,Alberto European Hairspray (Aerosol) - All Variants,,,aerosol hairspray,"
            "0000075-37-6,hydrofluorocarbon 152a (difluoroethane),,0.39,0.42,1,,,Test Component"
            "\n"
            "7,11165872.pdf,Alberto European Hairspray (Aerosol) - All Variants,,,aerosol hairspray,"
            "0000064-17-5,sd alcohol 40-b (ethanol),,0.5,0.55,1,,,Test Component"
            "\n"
            "7,11165872.pdf,Alberto European Hairspray (Aerosol) - All Variants,,,aerosol hairspray,"
            "0000064-17-6,sd alcohol 40-c (ethanol c),,,,2,,,Test Component"
            "\n"
            "7,11165872.pdf,Alberto European Hairspray (Aerosol) - All Variants,,,aerosol hairspray,"
            ",,,,,,,,"
        )
        sample_csv_bytes = csv_string.encode(encoding="UTF-8", errors="strict")
        in_mem_sample_csv = InMemoryUploadedFile(
            io.BytesIO(sample_csv_bytes),
            field_name="extfile-bulkformsetfileupload",
            name="British_Petroleum_(Air)_1_extract_template.csv",
            content_type="text/csv",
            size=len(csv_string),
            charset="utf-8",
        )
        return in_mem_sample_csv

    def generate_invalid_chem_csv(self):
        csv_string = (
            "data_document_id,data_document_filename,"
            "prod_name,doc_date,rev_num,raw_category,raw_cas,raw_chem_name,"
            "report_funcuse,raw_min_comp,raw_max_comp,unit_type,"
            "ingredient_rank,raw_central_comp,component"
            "\n"
            "8,11177849.pdf,Alberto European Hairspray (Aerosol) - All Variants,,,aerosol hairspray,"
            "0000075-37-6,hydrofluorocarbon 152a (difluoroethane),,0.39,0.42,1,,"
            "\n"
            "8,11177849.pdf,A different prod_name with the same datadocument,,,aerosol hairspray,"
            "0000064-17-5,sd alcohol 40-b (ethanol),,0.5,0.55,1,,"
        )
        sample_csv_bytes = csv_string.encode(encoding="UTF-8", errors="strict")
        in_mem_sample_csv = InMemoryUploadedFile(
            io.BytesIO(sample_csv_bytes),
            field_name="extfile-bulkformsetfileupload",
            name="British_Petroleum_(Air)_1_extract_template.csv",
            content_type="text/csv",
            size=len(csv_string),
            charset="utf-8",
        )
        return in_mem_sample_csv

    def test_chem_upload(self):
        req_data = {
            "extfile-extraction_script": 5,
            "extfile-weight_fraction_type": 1,
            "extfile-submit": "Submit",
        }
        req_data.update(self.mng_data)
        req = self.factory.post(path="/datagroup/6/", data=req_data)
        middleware = SessionMiddleware()
        middleware.process_request(req)
        req.session.save()
        middleware = MessageMiddleware()
        middleware.process_request(req)
        req.session.save()
        req.user = User.objects.get(username="Karyn")
        req.FILES["extfile-bulkformsetfileupload"] = self.generate_invalid_chem_csv()
        # get error in response
        text_count = ExtractedText.objects.all().count()
        resp = views.data_group_detail(request=req, pk=6)
        self.assertContains(resp, "must be 1:1")
        post_text_count = ExtractedText.objects.all().count()
        self.assertEquals(
            text_count, post_text_count, "Shouldn't have extracted texts uploaded"
        )
        # Now get the success response
        req.FILES["extfile-bulkformsetfileupload"] = self.generate_valid_chem_csv()
        doc_count = DataDocument.objects.filter(
            raw_category="aerosol hairspray"
        ).count()
        old_rawchem_count = RawChem.objects.filter().count()
        old_extractedchemical_count = ExtractedChemical.objects.filter().count()
        self.assertTrue(
            doc_count == 0, "DataDocument raw category shouldn't exist yet."
        )
        resp = views.data_group_detail(request=req, pk=6)
        self.assertContains(resp, "4 extracted records uploaded successfully.")
        new_rawchem_count = RawChem.objects.filter().count()
        new_extractedchemical_count = ExtractedChemical.objects.filter().count()
        self.assertTrue(
            new_rawchem_count - old_rawchem_count == 3,
            "There should only be 3 new RawChem records",
        )
        self.assertTrue(
            new_extractedchemical_count - old_extractedchemical_count == 3,
            "There should only be 3 new ExtractedChemical records",
        )
        doc_count = DataDocument.objects.filter(
            raw_category="aerosol hairspray"
        ).count()
        self.assertTrue(
            doc_count > 0, "DataDocument raw category values must be updated."
        )
        text_count = ExtractedText.objects.all().count()
        self.assertTrue(text_count == 2, "Should be 2 extracted texts")
        chem_count = ExtractedChemical.objects.filter(
            component="Test Component"
        ).count()
        self.assertTrue(
            chem_count == 3,
            "Should be 3 extracted chemical records with the Test Component",
        )
        dg = DataGroup.objects.get(pk=6)
        dg.delete()

    def test_presence_upload(self):
        # Delete the CPCat records that were loaded with the fixtures
        ExtractedCPCat.objects.all().delete()
        self.assertEqual(
            len(ExtractedCPCat.objects.all()), 0, "Should be empty before upload."
        )
        usr = User.objects.get(username="Karyn")
        # test for error to be propagated w/o a 1:1 match of ExtCPCat to DataDoc
        in_mem_sample_csv = make_upload_csv("sample_files/presence_cpcat.csv")
        req_data = {"extfile-extraction_script": 5, "extfile-submit": "Submit"}
        req_data.update(self.mng_data)
        req = self.factory.post("/datagroup/49/", data=req_data)
        req.FILES["extfile-bulkformsetfileupload"] = in_mem_sample_csv
        middleware = SessionMiddleware()
        middleware.process_request(req)
        req.session.save()
        middleware = MessageMiddleware()
        middleware.process_request(req)
        req.session.save()
        req.user = usr
        resp = views.data_group_detail(request=req, pk=49)
        self.assertContains(resp, "must be 1:1")
        self.assertEqual(
            len(ExtractedCPCat.objects.all()),
            0,
            "ExtractedCPCat records remain 0 if error in upload.",
        )
        # test for error to propogate w/ too many chars in a field
        in_mem_sample_csv = make_upload_csv("sample_files/presence_chars.csv")
        req.FILES["extfile-bulkformsetfileupload"] = in_mem_sample_csv
        resp = views.data_group_detail(request=req, pk=49)
        self.assertContains(resp, "Ensure this value has at most 50 characters")
        self.assertEqual(
            len(ExtractedCPCat.objects.all()),
            0,
            "ExtractedCPCat records remain 0 if error in upload.",
        )
        # test that upload works successfully...
        in_mem_sample_csv = make_upload_csv("sample_files/presence_good.csv")
        req.FILES["extfile-bulkformsetfileupload"] = in_mem_sample_csv
        resp = views.data_group_detail(request=req, pk=49)
        self.assertContains(resp, "3 extracted records uploaded successfully.")

        doc_count = DataDocument.objects.filter(
            raw_category="list presence category"
        ).count()
        self.assertTrue(
            doc_count > 0, "DataDocument raw category values must be updated."
        )
        self.assertEqual(len(ExtractedCPCat.objects.all()), 2, "Two after upload.")
        chem = ExtractedListPresence.objects.get(raw_cas__icontains="100784-20-1")
        self.assertTrue(chem.raw_cas[0] != " ", "White space should be stripped.")
        dg = DataGroup.objects.get(pk=49)
        dg.delete()

    def test_functionaluse_upload(self):
        # This action is performed on a data document without extracted text
        # but with a matched data document. DataDocument 500 was added to the
        # seed data for this test
        dd_id = 500
        dd = DataDocument.objects.get(pk=dd_id)
        # et = ExtractedText.objects.get(data_document=dd)
        dd_pdf = dd.pdf_url()

        sample_csv = (
            "data_document_id,data_document_filename,prod_name,"
            "doc_date,rev_num,raw_category,raw_cas,raw_chem_name,report_funcuse"
            "\n"
            "%s,"
            "%s,"
            "sample functional use product,"
            "2018-04-07,"
            ","
            "raw PUC,"
            "RAW-CAS-01,"
            "raw chemname 01,"
            "surfactant" % (dd_id, dd_pdf)
        )
        sample_csv_bytes = sample_csv.encode(encoding="UTF-8", errors="strict")
        in_mem_sample_csv = InMemoryUploadedFile(
            io.BytesIO(sample_csv_bytes),
            field_name="extfile-bulkformsetfileupload",
            name="Functional_use_extract_template.csv",
            content_type="text/csv",
            size=len(sample_csv),
            charset="utf-8",
        )
        req_data = {"extfile-extraction_script": 5, "extfile-submit": "Submit"}
        req_data.update(self.mng_data)
        req = self.factory.post("/datagroup/50/", data=req_data)
        req.FILES["extfile-bulkformsetfileupload"] = in_mem_sample_csv
        middleware = SessionMiddleware()
        middleware.process_request(req)
        req.session.save()
        middleware = MessageMiddleware()
        middleware.process_request(req)
        req.session.save()
        req.user = User.objects.get(username="Karyn")
        self.assertEqual(
            len(ExtractedFunctionalUse.objects.filter(extracted_text_id=dd_id)),
            0,
            "Empty before upload.",
        )
        # Now get the response
        resp = views.data_group_detail(request=req, pk=50)
        self.assertContains(resp, "1 extracted record uploaded successfully.")

        doc_count = DataDocument.objects.filter(raw_category="raw PUC").count()
        self.assertTrue(
            doc_count > 0, "DataDocument raw category values must be updated."
        )

        self.assertEqual(
            len(ExtractedFunctionalUse.objects.filter(extracted_text_id=dd_id)),
            1,
            "One new ExtractedFunctionalUse after upload.",
        )
