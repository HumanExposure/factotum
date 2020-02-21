import os
import io

from django.test import RequestFactory, TestCase, Client
from django.contrib.auth.models import User
from django.utils.datastructures import MultiValueDict
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware

from django.conf import settings
from dashboard import views
from dashboard.models import *
from dashboard.tests.loader import fixtures_standard
from dashboard.tests.mixins import TempFileMixin


class RegisterRecordsTest(TempFileMixin, TestCase):
    fixtures = fixtures_standard

    def setUp(self):
        self.factory = RequestFactory()
        self.client.login(username="Karyn", password="specialP@55word")

    def test_datagroup_create(self):
        long_fn = "a filename that is too long " * 10
        csv_string = (
            "filename,title,document_type,url,organization\n"
            "0bf5755e-3a08-4024-9d2f-0ea155a9bd17.pdf,NUTRA NAIL,MS,, \n"
            f"{long_fn},Body Cream,MS,, \n"
        )
        data = io.StringIO(csv_string)
        sample_csv = InMemoryUploadedFile(
            data,
            field_name="csv",
            name="register_records.csv",
            content_type="text/csv",
            size=len(csv_string),
            charset="utf-8",
        )
        form_data = {
            "name": ["Walmart MSDS Test Group"],
            "description": ["test data group"],
            "group_type": ["2"],
            "downloaded_by": [str(User.objects.get(username="Karyn").pk)],
            "downloaded_at": ["08/02/2018"],
            "download_script": ["1"],
            "data_source": ["10"],
        }
        request = self.factory.post(path="/datagroup/new/", data=form_data)
        request.FILES["csv"] = sample_csv
        request.user = User.objects.get(username="Karyn")
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()
        middleware = MessageMiddleware()
        middleware.process_request(request)
        request.session.save()
        request.session = {}
        request.session["datasource_title"] = "Walmart"
        request.session["datasource_pk"] = 10
        resp = views.data_group_create(request=request, pk=10)
        dg_exists = DataGroup.objects.filter(name="Walmart MSDS Test Group").exists()
        self.assertContains(
            resp, "filename: Ensure this value has at most 255 characters"
        )
        self.assertFalse(dg_exists)

        csv_string = (
            "filename,title,document_type,url,organization\n"
            "0bf5755e-3a08-4024-9d2f-0ea155a9bd17.pdf,NUTRA NAIL,MS,, \n"
            "0c68ab16-2065-4d9b-a8f2-e428eb192465.pdf,Body Cream,MS,, \n"
        )
        data = io.StringIO(csv_string)
        sample_csv = InMemoryUploadedFile(
            data,
            field_name="csv",
            name="register_records.csv",
            content_type="text/csv",
            size=len(csv_string),
            charset="utf-8",
        )
        request = self.factory.post(path="/datagroup/new", data=form_data)
        request.FILES["csv"] = sample_csv
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()
        middleware = MessageMiddleware()
        middleware.process_request(request)
        request.session.save()
        request.user = User.objects.get(username="Karyn")
        request.session = {}
        request.session["datasource_title"] = "Walmart"
        request.session["datasource_pk"] = 10
        resp = views.data_group_create(request=request, pk=10)

        self.assertEqual(resp.status_code, 302, "Should be redirecting")

        dg = DataGroup.objects.get(name="Walmart MSDS Test Group")

        self.assertEqual(
            f"/datagroup/{dg.pk}/", resp.url, "Should be redirecting to the proper URL"
        )

        # In the Data Group Detail Page
        resp = self.client.get(f"/datagroup/{dg.pk}/")

        # test whether the data documents were created
        docs = DataDocument.objects.filter(data_group=dg)
        self.assertEqual(len(docs), 2, "there should be two associated documents")

        # test whether the "Download Registered Records" link is like this example

        # <a href="/datagroup/a9c7f5a7-5ad4-4f75-b877-a3747f0cc081/download_registered_documents" class="btn btn-secondary">
        csv_href = f"/datagroup/{dg.pk}/download_registered_documents/"
        self.assertIn(
            csv_href,
            str(resp._container),
            "The data group detail page must contain the right download link",
        )

        # grab a filename from a data document and see if it's in the csv
        doc_fn = docs.first().filename
        # test whether the registered records csv download link works
        resp_rr_csv = self.client.get(
            csv_href
        )  # this object should be of type StreamingHttpResponse
        docfound = "not found"
        for csv_row in resp_rr_csv.streaming_content:
            if doc_fn in str(csv_row):
                docfound = "found"
        self.assertEqual(
            docfound,
            "found",
            "the document file name should appear in the registered records csv",
        )

        # Test whether the data document csv download works
        # URL on data group detail page: datagroup/docs_csv/{pk}/
        dd_csv_href = (
            f"/datagroup/{dg.pk}/download_documents/"
        )  # this is an interpreted django URL
        resp_dd_csv = self.client.get(dd_csv_href)
        for csv_row in resp_dd_csv.streaming_content:
            if doc_fn in str(csv_row):
                docfound = "found"
        self.assertEqual(
            docfound,
            "found",
            "the document file name should appear in the data documents csv",
        )

        # test uploading one pdf that matches a registered record
        doc = DataDocument.objects.filter(data_group_id=dg.pk).first()
        pdf = TemporaryUploadedFile(
            name=doc.filename, content_type="application/pdf", size=47, charset=None
        )
        request = self.factory.post(
            path="/datagroup/%s" % dg.pk, data={"uploaddocs-submit": "Submit"}
        )
        request.FILES["uploaddocs-documents"] = pdf
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()
        middleware = MessageMiddleware()
        middleware.process_request(request)
        request.session.save()
        request.user = User.objects.get(username="Karyn")
        resp = views.data_group_detail(request=request, pk=dg.pk)
        doc.refresh_from_db()
        pdf_path = doc.file.path
        self.assertTrue(
            os.path.exists(pdf_path), "the stored file should be in MEDIA_ROOT"
        )
        pdf.close()

    def test_datagroup_create_dupe_filename(self):
        csv_string = (
            "filename,title,document_type,url,organization\n"
            "0bf5755e-3a08-4024-9d2f-0ea155a9bd17.pdf,NUTRA NAIL,MS,, \n"
            "0bf5755e-3a08-4024-9d2f-0ea155a9bd17.pdf,Body Cream,MS,, \n"
        )
        data = io.StringIO(csv_string)
        sample_csv = InMemoryUploadedFile(
            data,
            field_name="csv",
            name="register_records.csv",
            content_type="text/csv",
            size=len(csv_string),
            charset="utf-8",
        )
        form_data = {
            "name": ["Walmart MSDS Test Group"],
            "description": ["test data group"],
            "group_type": ["2"],
            "downloaded_by": [str(User.objects.get(username="Karyn").pk)],
            "downloaded_at": ["08/02/2018"],
            "download_script": ["1"],
            "data_source": ["10"],
        }
        request = self.factory.post(path="/datagroup/new/", data=form_data)
        request.FILES["csv"] = sample_csv
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()
        middleware = MessageMiddleware()
        middleware.process_request(request)
        request.session.save()
        request.user = User.objects.get(username="Karyn")
        request.session = {}
        request.session["datasource_title"] = "Walmart"
        request.session["datasource_pk"] = 10
        resp = views.data_group_create(request=request, pk=10)

        self.assertContains(
            resp,
            "Duplicate &quot;filename&quot; values for &quot;"
            "0bf5755e-3a08-4024-9d2f-0ea155a9bd17.pdf&quot; are not allowed.",
        )

    def test_datagroup_create_url_len_err(self):
        long_url = "http://www.epa.gov" * 16
        csv_string = (
            "filename,title,document_type,url,organization\n"
            "0bf5755e-3a08-4024-9d2f-0ea155a9bd17.pdf,NUTRA NAIL,MS,, \n"
            f"another.pdf,Body Cream,MS,{long_url}, \n"
        )
        data = io.StringIO(csv_string)
        sample_csv = InMemoryUploadedFile(
            data,
            field_name="csv",
            name="register_records.csv",
            content_type="text/csv",
            size=len(csv_string),
            charset="utf-8",
        )
        form_data = {
            "name": ["Walmart MSDS Test Group"],
            "description": ["test data group"],
            "group_type": ["2"],
            "downloaded_by": [str(User.objects.get(username="Karyn").pk)],
            "downloaded_at": ["08/02/2018"],
            "download_script": ["1"],
            "data_source": ["10"],
        }
        request = self.factory.post(path="/datagroup/new/", data=form_data)
        request.FILES["csv"] = sample_csv
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()
        middleware = MessageMiddleware()
        middleware.process_request(request)
        request.session.save()
        request.user = User.objects.get(username="Karyn")
        request.session = {}
        request.session["datasource_title"] = "Walmart"
        request.session["datasource_pk"] = 10
        resp = views.data_group_create(request=request, pk=10)
        self.assertContains(resp, "url: Enter a valid URL")

    def test_csv_line_endings(self):
        csv_string = (
            "filename,title,document_type,url,organization\r"
            "0bf5755e-3a08-4024-9d2f-0ea155a9bd17.pdf,NUTRA NAIL,MS,, \r"
            "0c68ab16-2065-4d9b-a8f2-e428eb192465.pdf,Body Cream,MS,, \r\n"
        )
        data = io.StringIO(csv_string)
        sample_csv = InMemoryUploadedFile(
            data,
            field_name="csv",
            name="register_records.csv",
            content_type="text/csv",
            size=len(csv_string),
            charset="utf-8",
        )
        form_data = {
            "name": ["Walmart MSDS Test Group"],
            "description": ["test data group"],
            "group_type": ["2"],
            "downloaded_by": [f"{User.objects.first().pk}"],
            "downloaded_at": ["08/02/2018"],
            "download_script": ["1"],
            "data_source": ["10"],
        }
        request = self.factory.post(path="/datagroup/new/", data=form_data)
        request.FILES["csv"] = sample_csv
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()
        middleware = MessageMiddleware()
        middleware.process_request(request)
        request.session.save()
        request.user = User.objects.get(username="Karyn")
        request.session = {"datasource_title": "Walmart", "datasource_pk": 10}
        resp = views.data_group_create(request=request, pk=10)
        dg = DataGroup.objects.filter(name="Walmart MSDS Test Group")
        self.assertTrue(resp.status_code == 302, "Redirect to detail page")
        self.assertTrue(dg.exists(), "Group should be created")
