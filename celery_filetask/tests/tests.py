import io

from django.core.files.uploadedfile import UploadedFile

from celery_djangotest.unit import SimpleTestCase

from celery_filetask.contexts import filekeyinputs
from celery_filetask.utils import deletefilekeys, isfilekey
from celery_filetask.tests.tasks import getfilecontents, getfiletype, getfilename


class TestUserTasks(SimpleTestCase):
    def setUp(self):
        self.file = UploadedFile(io.StringIO("test contents"), name="test.txt")

    def test_filecontents(self):
        result = getfilecontents.delay(self.file).get()
        self.assertEqual(result, "test contents")

    def test_filetype(self):
        result = getfiletype.delay(self.file).get()
        self.assertEqual(
            result, "<class 'django.core.files.uploadedfile.UploadedFile'>"
        )

    def test_filename(self):
        result = getfilename.delay(self.file).get()
        self.assertEqual(result, "test.txt")

    def test_filenested(self):
        class FileNested:
            def __init__(self, file):
                filetuple = ([{"file": file}],)
                filetuple[0][0]["recursive"] = filetuple
                self.filetuple = filetuple

        with filekeyinputs((FileNested(self.file),), {}) as inputs:
            self.assertTrue(
                isfilekey((None, None, inputs[0][0].filetuple[0][0]["file"]))
            )
        deletefilekeys(inputs)
