import io
from lxml import html

from django.utils import timezone
from django.test import RequestFactory, TestCase, override_settings
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware

from dashboard.models import *
from dashboard.tests.loader import *
from dashboard.views.data_group import DataGroupForm, data_group_create


@override_settings(ALLOWED_HOSTS=["testserver"])
class DataGroupFormTest(TestCase):
    fixtures = fixtures_standard

    def setUp(self):
        self.factory = RequestFactory()
        self.client.login(username="Karyn", password="specialP@55word")

    def test_detail_form(self):
        self.assertTrue(
            DataGroupForm().fields["url"], "DataGroupForm should include the url"
        )

        dg = DataGroup.objects.get(pk=6)
        response = self.client.get(f"/datagroup/edit/{dg.pk}/")
        self.assertNotIn("csv", response.context["form"].fields)
        response = self.client.post(
            f"/datagroup/edit/{dg.pk}/",
            {
                "name": dg.name,
                "url": "http://www.epa.gov",
                "group_type": dg.group_type_id,
                "downloaded_by": dg.downloaded_by_id,
                "downloaded_at": dg.downloaded_at,
                "data_source": dg.data_source_id,
            },
        )
        dg.refresh_from_db()
        dg = DataGroup.objects.get(pk=dg.pk)
        self.assertEqual(
            dg.url,
            "http://www.epa.gov",
            f'DataDocument {dg.pk} should have the url "http://www.epa.gov"',
        )

        # URL needs to include a schema (e.g., "http://" to be valid)
        response = self.client.post(
            f"/datagroup/edit/{dg.pk}/",
            {
                "name": dg.name,
                "url": "www.epa.gov",
                "group_type": dg.group_type_id,
                "downloaded_by": dg.downloaded_by_id,
                "downloaded_at": dg.downloaded_at,
                "data_source": dg.data_source_id,
            },
        )
        self.assertContains(response, "Enter a valid URL")

    def test_detail_form_group_type(self):
        # The group type should not be an editable field in the data group update page
        dg = DataGroup.objects.get(pk=6)
        response = self.client.get(f"/datagroup/edit/{str(dg.pk)}/").content.decode(
            "utf8"
        )
        response_html = html.fromstring(response)
        group_type_field = response_html.xpath('//*[@id="id_group_type"]')
        self.assertTrue(
            group_type_field == [], "There should be no form field for group_type"
        )
        group_type_before = dg.group_type
        response = self.client.post(
            f"/datagroup/edit/{dg.pk}/",
            {
                "name": dg.name,
                "description": "An edited data group",
                "url": "http://www.epa.gov",
                "group_type": dg.group_type_id + 1,
                "downloaded_by": dg.downloaded_by_id,
                "downloaded_at": dg.downloaded_at,
                "data_source": dg.data_source_id,
            },
            follow=True,
        )

        response_html = html.fromstring(response.content.decode("utf8"))

        self.assertEqual(
            dg.group_type,
            group_type_before,
            "Submitting a different group_type in a POST should not change the object",
        )

    def test_register_records_header(self):
        ds_pk = DataSource.objects.first().pk
        csv_string = (
            "filename,title,document_type,product,url,organization\n"
            "1.pdf,Home Depot,2,,www.homedepot.com/594.pdf,\n"
            "2.pdf,Home Depot,2,,www.homedepot.com/fb5.pdf,\n"
        )
        csv_string_bytes = csv_string.encode(encoding="UTF-8", errors="strict")
        in_mem_sample_csv = InMemoryUploadedFile(
            io.BytesIO(csv_string_bytes),
            field_name="register_records",
            name="register_records.csv",
            content_type="text/csv",
            size=len(csv_string),
            charset="utf-8",
        )
        data = {
            "name": "Slinky",
            "group_type": 1,
            "downloaded_by": 1,
            "downloaded_at": timezone.now(),
            "download_script": 1,
            "data_source": ds_pk,
            "csv": in_mem_sample_csv,
        }
        request = self.factory.post(
            path=f"/datasource/{ds_pk}/datagroup_new/", data=data
        )

        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()
        middleware = MessageMiddleware()
        middleware.process_request(request)

        request.session.save()
        request.user = User.objects.get(username="Karyn")
        resp = data_group_create(request=request, pk=6)
        self.assertContains(
            resp,
            "CSV column titles should be [&#39;filename&#39;, &#39;title&#39;,"
            " &#39;document_type&#39;, &#39;url&#39;, &#39;organization&#39;]",
        )
