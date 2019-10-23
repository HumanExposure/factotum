import io
import uuid
import random

from django import forms
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.test import SimpleTestCase

from .forms import bulkformset_factory
from .utils import BulkMuxDict
from .serializers import CSVReader


class SampleForm(forms.Form):
    gibberish = forms.CharField()
    number = forms.IntegerField()


class BulkMuxDictTest(SimpleTestCase):
    def setUp(self):
        self.num_cols = 10
        self.num_rows = 10
        self.headers = set(str(uuid.uuid4()) for i in range(self.num_cols))
        self.data_vals = {h: str(uuid.uuid4()) for h in self.headers}
        self.data = {
            "form-TOTAL_FORMS": "1",
            "form-INITIAL_FORMS": "0",
            "form-MAX_NUM_FORMS": "",
        }
        self.data.update({"form-0-%s" % k: v for k, v in self.data_vals.items()})
        self.bulk = [
            {h: str(uuid.uuid4()) for h in self.headers}
            for i in range(self.num_rows - 1)
        ]
        self.mux = BulkMuxDict(self.data, self.bulk, set(), "form")

    def test_len(self):
        self.assertEqual(self.num_cols * self.num_rows + 3, len(self.mux))
        self.assertEqual(self.num_rows, int(self.mux["form-TOTAL_FORMS"]))

    def test_get(self):
        for h in self.headers:
            k = "form-0-%s" % h
            self.assertEqual(self.data[k], self.mux[k])
        for i, d in enumerate(self.bulk):
            for h, v in d.items():
                if i == 0:
                    k = "form-%d-%s" % (i, h)
                    self.assertEqual(self.data_vals[h], self.mux[k])
                else:
                    k = "form-%d-%s" % (i + 1, h)
                    self.assertEqual(v, self.mux[k])
        out_of_bounds_key = "form-%d-%s" % (self.num_rows + 1, self.headers.pop())
        self.assertRaises(KeyError, lambda x: self.mux[x], out_of_bounds_key)

    def test_iter(self):
        valid_i = set(i for i in range(self.num_rows))
        for f in self.mux:
            if f not in {
                "form-TOTAL_FORMS",
                "form-INITIAL_FORMS",
                "form-MAX_NUM_FORMS",
            }:
                i, k = self.mux.parse_key(f)
                self.assertIn(i, valid_i)
                self.assertIn(k, self.headers)
        for f, v in self.mux.items():
            if f not in {
                "form-TOTAL_FORMS",
                "form-INITIAL_FORMS",
                "form-MAX_NUM_FORMS",
            }:
                i, k = self.mux.parse_key(f)
                self.assertIn(i, valid_i)
                self.assertIn(k, self.headers)
                if i == 0:
                    self.assertEqual(v, self.data_vals[k])
                else:
                    self.assertEqual(v, self.bulk[i - 1][k])


class CSVReaderTest(SimpleTestCase):
    def setUp(self):
        self.num_cols = 10
        self.num_rows = 10
        self.data = tuple(
            tuple(str(uuid.uuid4()) for i in range(self.num_cols))
            for j in range(self.num_rows)
        )
        self.csv_str = "\n".join(",".join(c for c in r) for r in self.data) + "\n\n"

    def _mk_file(self):
        return InMemoryUploadedFile(
            io.StringIO(self.csv_str),
            field_name="csv",
            name="register_records.csv",
            content_type="text/csv",
            size=len(self.csv_str),
            charset="utf-8",
        )

    def test_get(self):
        s = CSVReader(self._mk_file())
        rand_rows = (random.randint(0, len(s) - 1) for i in range(100))
        for i in rand_rows:
            j = random.randint(0, self.num_cols - 1)
            key = s.fieldnames[j]
            value = self.data[i + 1][j]
            self.assertEqual(value, s[i][key])

    def test_iter(self):
        s = CSVReader(self._mk_file())
        for i, d in enumerate(s):
            for ref, res in zip(zip(self.data[0], self.data[i + 1]), d.items()):
                self.assertEqual(ref, res)

    def test_len(self):
        s = CSVReader(self._mk_file())
        self.assertEqual(self.num_rows - 1, len(s))
        max_num_s = CSVReader(self._mk_file(), max_num=3)
        self.assertEqual(4, len(max_num_s))


class BulkFormSetTest(SimpleTestCase):
    """Above we have tested that our BulkMuxDict works like an immutable dictionary.
    Since this is exactly what the underlying class of BulkFormSet expects, we can
    assume all functionality of FormSet acts as intended except what we've overridden.
    """

    def test_init(self):
        csv_str = "gibberish,number\nha,1\nlol,2"
        f = {
            "form-bulkformsetfileupload": InMemoryUploadedFile(
                io.StringIO(csv_str),
                field_name="csv",
                name="register_records.csv",
                content_type="text/csv",
                size=len(csv_str),
                charset="utf-8",
            )
        }
        d = {
            "form-TOTAL_FORMS": "0",
            "form-INITIAL_FORMS": "0",
            "form-MAX_NUM_FORMS": "",
        }
        SampleFormBulkFormSet = bulkformset_factory(SampleForm, serializer=CSVReader)
        self.assertTrue(SampleFormBulkFormSet.__name__ == "SampleFormBulkFormSet")
        s = SampleFormBulkFormSet(d, f)
        self.assertTrue(type(s.data) == BulkMuxDict)
        self.assertTrue("max_num" in s.serializer_kwargs)
