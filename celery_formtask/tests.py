import json

from django import forms
from django.test import Client, override_settings
from celery_formtask.forms import FormTaskMixin
from celery_djangotest.unit import TransactionTestCase


class SampleForm(forms.Form):
    i = forms.IntegerField(max_value=1)


class SampleFormTask(FormTaskMixin, SampleForm):
    def save(self):
        return True


class SampleFormSetTask(FormTaskMixin, forms.BaseFormSet):
    form = SampleForm
    extra = 1
    can_order = False
    can_delete = False
    min_num = 0
    max_num = 1
    absolute_max = 1
    validate_min = False
    validate_max = False

    def save(self):
        return True


class InvalidSampleFormSetTask(SampleFormSetTask):
    def clean(self):
        raise forms.ValidationError("test")


@override_settings(ROOT_URLCONF="celery_resultsview.urls")
class TestFormTask(TransactionTestCase):
    def setUp(self):
        self.c = Client()

    def get(self, url):
        response = self.c.get(url)
        return json.loads(response.content)

    def _test_invalid(self, task_id, data):
        self.assertTrue(task_id in data)
        self.assertTrue("status" in data[task_id])
        self.assertEqual("FAILURE", data[task_id]["status"])
        self.assertTrue("result" in data[task_id])

    def test_form(self):
        form = SampleFormTask({"i": 1})
        asyncresult = form.enqueue()
        self.assertTrue(asyncresult.get())

    def test_invalidform(self):
        form = SampleFormTask({"i": 2})
        asyncresult = form.enqueue()
        asyncresult.wait(propagate=False)
        data = self.get(f"/{asyncresult.id}/")
        self._test_invalid(asyncresult.id, data)
        self.assertTrue("form_errors" in data[asyncresult.id]["result"])

    def test_formset(self):
        data = {
            "form-TOTAL_FORMS": "1",
            "form-INITIAL_FORMS": "0",
            "form-MAX_NUM_FORMS": "",
            "form-0-i": 1,
        }
        formset = SampleFormSetTask(data)
        asyncresult = formset.enqueue()
        self.assertTrue(asyncresult.get())

    def test_invalidformset(self):
        data = {
            "form-TOTAL_FORMS": "1",
            "form-INITIAL_FORMS": "0",
            "form-MAX_NUM_FORMS": "",
            "form-0-i": 2,
        }
        formset = InvalidSampleFormSetTask(data)
        asyncresult = formset.enqueue()
        asyncresult.wait(propagate=False)
        data = self.get(f"/{asyncresult.id}/")
        self._test_invalid(asyncresult.id, data)
        self.assertTrue("form_errors" in data[asyncresult.id]["result"])
        self.assertTrue("non_form_errors" in data[asyncresult.id]["result"])
