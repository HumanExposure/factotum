from django.urls import resolve
from django.test import RequestFactory, TestCase, Client, override_settings
from django.test.client import Client
from django.core.files.uploadedfile import InMemoryUploadedFile

from django.contrib.auth.models import User
from django.contrib.auth import authenticate

from dashboard import views
from dashboard.tests.loader import fixtures_standard
from django.contrib import messages
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from dashboard.models import DataDocument

import tempfile
import csv
import os
import io
import shutil
from pathlib import Path


def string_to_csv(csv_string):
    """
    Encode a string as bytes and convert to an InMemoryUploadedFile
    """
    csv_bytes = csv_string.encode(encoding="UTF-8", errors="strict")
    in_mem_csv = InMemoryUploadedFile(
        io.BytesIO(csv_bytes),
        field_name="csv_file",
        name="data_documents.csv",
        content_type="text/csv",
        size=len(csv_string),
        charset="utf-8",
    )
    return in_mem_csv


@override_settings(ALLOWED_HOSTS=["testserver"])
class TestZipPDFs(TestCase):

    fixtures = fixtures_standard

    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()
        self.client.login(username="Karyn", password="specialP@55word")
        self.mng_data = {
            "form-TOTAL_FORMS": "0",
            "form-INITIAL_FORMS": "0",
            "form-MAX_NUM_FORMS": "",
        }
        # mk fake files
        for d in DataDocument.objects.filter(pk__in=[122079, 121831, 121722, 121698]):
            p = Path(f".{d.pdf_url()}")
            p.parent.mkdir(parents=True, exist_ok=True)
            p.touch()

    def tearDown(self):
        # rm fake files
        shutil.rmtree("./media/3dada08f-91aa-4e47-9556-e3e1a23b1d7e")

    def test_zip_pdfs_small(self):
        """
        Upload a four-row csv file with the correct column id
        """
        req = self.factory.post(path="/bulk_documents/", data=self.mng_data)
        req.user = User.objects.get(username="Karyn")
        csv_string = "id" "\n" "122079" "\n" "121831" "\n" "121722" "\n" "121698"
        in_mem_csv = string_to_csv(csv_string)
        req.FILES["form-bulkformsetfileupload"] = in_mem_csv
        resp = views.BulkDocuments.as_view()(request=req)
        self.assertEqual(resp.status_code, 200)

    def test_zip_pdfs_missing(self):
        """
        Upload a csv file with the correct column id
        but with document IDs that don't have pdfs
        """
        req = self.factory.post(path="/bulk_documents/", data=self.mng_data)
        # Annotate a request object with a session
        middleware = SessionMiddleware()
        middleware.process_request(req)
        req.session.save()
        # Annotate a request object with a messages
        middleware = MessageMiddleware()
        middleware.process_request(req)
        req.session.save()
        req.user = User.objects.get(username="Karyn")
        DataDocument.objects.filter(pk__in=[121722, 121698]).update(matched=False)
        csv_string = "id" "\n" "122079" "\n" "121831" "\n" "121722" "\n" "121698"
        in_mem_csv = string_to_csv(csv_string)
        req.FILES["form-bulkformsetfileupload"] = in_mem_csv
        resp = views.BulkDocuments.as_view()(request=req)
        self.assertEqual(resp.status_code, 206)

    def test_zip_pdfs_bad_header(self):
        """
        Upload a csv file with the wrong column id
        """
        req = self.factory.post(path="/bulk_documents/", data=self.mng_data)
        # Add the necessary middleware objects to the request
        """Annotate a request object with a session"""
        middleware = SessionMiddleware()
        middleware.process_request(req)
        req.session.save()

        """Annotate a request object with a messages"""
        middleware = MessageMiddleware()
        middleware.process_request(req)
        req.session.save()
        req.user = User.objects.get(username="Karyn")
        csv_string = "bad_id" "\n" "122079" "\n" "121831" "\n" "121722" "\n" "121698"
        in_mem_csv = string_to_csv(csv_string)
        req.FILES["form-bulkformsetfileupload"] = in_mem_csv
        # It should redirect because of the error
        resp = views.BulkDocuments.as_view()(request=req)
        resp.client = self.client
        self.assertRedirects(resp, "/bulk_documents/", status_code=302)
