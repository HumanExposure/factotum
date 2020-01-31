import io
from datetime import datetime

from django.test import RequestFactory, TestCase, Client
from django.contrib.auth.models import User
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.files.uploadedfile import InMemoryUploadedFile

from dashboard import views
from dashboard.models import Product, DataDocument, ProductDocument
from dashboard.tests.loader import fixtures_standard


class UploadProductTest(TestCase):
    fixtures = fixtures_standard

    def setUp(self):
        self.c = Client()
        self.factory = RequestFactory()
        self.c.login(username="Karyn", password="specialP@55word")

    def post_csv(self, sample_csv):
        """
        For DRY purposes, this method takes a csv string
        generated above and returns a POST request that includes it
        """
        sample_csv_bytes = sample_csv.encode(encoding="UTF-8", errors="strict")
        in_mem_sample_csv = InMemoryUploadedFile(
            io.BytesIO(sample_csv_bytes),
            field_name="products-bulkformsetfileupload",
            name="clean_product_data.csv",
            content_type="text/csv",
            size=len(sample_csv),
            charset="utf-8",
        )
        data = {
            "products-submit": "Submit",
            "products-TOTAL_FORMS": 0,
            "products-INITIAL_FORMS": 0,
            "products-MAX_NUM_FORMS": "",
            "products-bulkformsetfileupload": in_mem_sample_csv,
        }
        return self.c.post(path="/datagroup/23/", data=data, follow=True)

    def test_valid_product_data_upload(self):
        sample_csv = (
            "data_document_id,data_document_filename,title,upc,url,brand_name,size,color,item_id,parent_item_id,short_description,long_description,thumb_image,medium_image,large_image,model_number,manufacturer\n"
            "177852,fff53301-a199-4e1b-91b4-39227ca0fe3c.pdf,'product title a',110230011425\n"
            "178456,fefd813f-d1e0-4fa7-8c4e-49030eca08a3.pdf,'product title b',903944840750\n"
            "178496,fc5f964c-91e2-42c5-9899-2ff38e37ba89.pdf,'product title c',852646877466\n"
            "161698,f040f93d-1cf3-4eff-85a9-da14d8d2e252.pdf,'product title d'\n"
            "159270,f040f93d-1cf3-4eff-85a9-da14d8d2e253.pdf,'product title e'"
        )
        pre_pdcount = ProductDocument.objects.count()
        resp = self.post_csv(sample_csv)
        self.assertContains(resp, "5 records have been successfully uploaded.")
        # ProductDocument records should also have been added
        post_pdcount = ProductDocument.objects.count()
        self.assertEqual(
            post_pdcount,
            pre_pdcount + 5,
            "There should be 5 more ProductDocuments after the upload",
        )
        # The first data_document_id in the csv should now have
        # two Products linked to it, including the new one
        resp = self.c.get(f"/datadocument/%s/" % 177852)
        self.assertContains(resp, "product title a")

    def test_existing_upc_upload(self):
        """
        A UPC that exists in the database already should be rejected
        """
        sample_csv = (
            "data_document_id,data_document_filename,title,upc,url,brand_name,size,color,item_id,parent_item_id,short_description,long_description,thumb_image,medium_image,large_image,model_number,manufacturer\n"
            "162019,fff53301-a199-4e1b-91b4-39227ca0fe3c.pdf,'product title a',110230011425\n"
            "161990,fefd813f-d1e0-4fa7-8c4e-49030eca08a3.pdf,'product title b',903944840750\n"
            "161938,fc5f964c-91e2-42c5-9899-2ff38e37ba89.pdf,'product title c',852646877466\n"
            "161698,f040f93d-1cf3-4eff-85a9-da14d8d2e252.pdf,'product title d',stub_11"
        )
        resp = self.post_csv(sample_csv)
        self.assertContains(
            resp,
            "The following records had existing or duplicated UPCs and were not added: 161698",
        )
        self.assertContains(resp, "3 records have been successfully uploaded")

    def test_duplicate_upc_upload(self):
        """
        The duplicated UPCs in the file should result in both new rows
        being rejected
        """
        sample_csv = (
            "data_document_id,data_document_filename,title,upc,url,brand_name,size,color,item_id,parent_item_id,short_description,long_description,thumb_image,medium_image,large_image,model_number,manufacturer\n"
            "177852,fff53301-a199-4e1b-91b4-39227ca0fe3c.pdf,'product title a',110230011425\n"
            "178456,fefd813f-d1e0-4fa7-8c4e-49030eca08a3.pdf,'product title b',903944840750\n"
            "178496,fc5f964c-91e2-42c5-9899-2ff38e37ba89.pdf,'product title c',852646877466\n"
            "161698,f040f93d-1cf3-4eff-85a9-da14d8d2e252.pdf,'product title d'\n"
            "159270,f040f93d-1cf3-4eff-85a9-da14d8d2e253.pdf,'product title e',852646877466"
        )
        resp = self.post_csv(sample_csv)
        self.assertContains(
            resp,
            "The following records had existing or duplicated UPCs and were not added: 178496, 159270",
        )
        self.assertContains(resp, "3 records have been successfully uploaded.")

    def test_bad_header_upload(self):
        """
        The bad header should cause the entire form to be invalid
        """
        sample_csv = (
            "data_document_idX,data_document_file_name,title,upc,url,brand_name,size,color,item_id,parent_item_id,short_description,long_description,thumb_image,medium_image,large_image,model_number,manufacturer\n"
            "177852,fff53301-a199-4e1b-91b4-39227ca0fe3c.pdf,'product title a',110230011425\n"
            "178456,fefd813f-d1e0-4fa7-8c4e-49030eca08a3.pdf,'product title b',903944840750\n"
            "178496,fc5f964c-91e2-42c5-9899-2ff38e37ba89.pdf,'product title c',852646877466\n"
            "161698,f040f93d-1cf3-4eff-85a9-da14d8d2e252.pdf,'product title d'\n"
            "159270,f040f93d-1cf3-4eff-85a9-da14d8d2e253.pdf,'product title e'"
        )
        resp = self.post_csv(sample_csv)
        self.assertContains(resp, "data_document_filename: This field is required.")
        self.assertContains(resp, "CSV column titles should be ")

    def test_blank_upc_upload(self):
        """
        Each UPC should be made and be unique
        """
        sample_csv = (
            "data_document_id,data_document_filename,title,upc,url,brand_name,size,color,item_id,parent_item_id,short_description,long_description,thumb_image,medium_image,large_image,model_number,manufacturer\n"
            "177852,fff53301-a199-4e1b-91b4-39227ca0fe3c.pdf,'product title a'\n"
            "178456,fefd813f-d1e0-4fa7-8c4e-49030eca08a3.pdf,'product title b'\n"
            "178496,fc5f964c-91e2-42c5-9899-2ff38e37ba89.pdf,'product title c'\n"
            "161698,f040f93d-1cf3-4eff-85a9-da14d8d2e252.pdf,'product title d'\n"
            "159270,f040f93d-1cf3-4eff-85a9-da14d8d2e253.pdf,'product title e'"
        )
        pre_pdcount = ProductDocument.objects.count()
        resp = self.post_csv(sample_csv)
        self.assertContains(resp, "5 records have been successfully uploaded.")
        # ProductDocument records should also have been added
        post_pdcount = ProductDocument.objects.count()
        self.assertEqual(
            post_pdcount,
            pre_pdcount + 5,
            "There should be 5 more ProductDocuments after the upload",
        )
        # The first data_document_id in the csv should now have
        # two Products linked to it, including the new one
        resp = self.c.get(f"/datadocument/%s/" % 177852)
        self.assertContains(resp, "product title a")
