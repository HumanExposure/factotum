from django.urls import resolve
from django.test import RequestFactory, TestCase, Client
from django.http import HttpRequest
from dashboard import views
from dashboard.models import *
from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile, SimpleUploadedFile
import tempfile, csv, os, io, errno
from django.contrib.auth.models import User
from dashboard.tests.loader import fixtures_standard


def build_datagroup_folder(dirname,):
    fullpath = os.path.join(settings.MEDIA_ROOT, dirname)
    try:
        os.makedirs(fullpath)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
    pdfpath = os.path.join(settings.MEDIA_ROOT, dirname, "pdf")
    try:
        os.makedirs(pdfpath)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
    csv_string = (
        "filename,title,document_type,url,organization\n"
        "0bf5755e-3a08-4024-9d2f-0ea155a9bd17.pdf,NUTRA NAIL,1,, \n"
        "0c68ab16-2065-4d9b-a8f2-e428eb192465.pdf,Body Cream,1,, \n"
    )

    with open(
        f"{fullpath}/British_Petroleum_Air_1_British_Petroleum_Air_1_register_recor_EHDBt5f.csv",
        "w",
    ) as rr_csv:
        rr_csv.write(csv_string)
        rr_csv.close()


class DataGroupFileDownloadTest(TestCase):
    fixtures = fixtures_standard

    def setUp(self):
        self.c = Client()
        self.factory = RequestFactory()
        self.c.login(username="Karyn", password="specialP@55word")

    def tearDown(self):
        # clean up the file system by deleting the data group object
        dg = DataGroup.objects.get(pk=6)
        dg.delete()

    def test_old_path(self):
        """
        Before we switched to UUIDs for the data group media folders,
        the paths were based on the original name of the data group
        """
        testpath = "British_Petroleum_(Air)_1"
        build_datagroup_folder(testpath)
        # the get_dg_folder() method should be able to find the newly-created directory
        dg = DataGroup.objects.get(pk=6)
        self.assertEqual(
            testpath,
            dg.get_dg_folder().rsplit("/")[-1],
            "The get_dg_folder() method should have returned the newly created directory",
        )

    def test_get_dg_folder(self):
        """
        The dev environment does not contain folders for most of the datagroups,
        so this just tests whether the methods can return their messages without
        errors.
        """
        for dg in DataGroup.objects.all():
            with self.assertRaises(Exception):
                try:
                    folderpath = dg.get_dg_folder()
                    zippath = dg.get_zip_url()
                except:
                    pass
                else:
                    raise Exception
