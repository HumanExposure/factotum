import json

from django.test import Client, override_settings

from celery_djangotest.unit import TransactionTestCase

from celery_resultsview.tests.tasks import task


@override_settings(ROOT_URLCONF="celery_resultsview.urls")
class TestResultsView(TransactionTestCase):
    def setUp(self):
        r1 = task.delay()
        r2 = task.delay()
        r1.wait()
        r2.wait()
        self.task_ids = [r1.id, r2.id]
        self.c = Client()

    def get(self, url):
        response = self.c.get(url)
        return json.loads(response.content)

    def _test_task_id(self, task_id, data):
        self.assertTrue(task_id in data)
        self.assertTrue("status" in data[task_id])
        self.assertEquals("SUCCESS", data[task_id]["status"])
        self.assertTrue("result" in data[task_id])
        self.assertTrue(data[task_id]["result"])

    def test_novalid(self):
        data = self.get(f"/invalid/")
        self.assertEquals({}, data)

    def test_one(self):
        task_id = self.task_ids[0]
        data = self.get(f"/{task_id}/")
        self._test_task_id(task_id, data)

    def test_many(self):
        task_ids = ",".join(self.task_ids)
        data = self.get(f"/{task_ids}/")
        for task_id in self.task_ids:
            self._test_task_id(task_id, data)

    def test_delete(self):
        task_ids = ",".join(self.task_ids)
        response = self.c.delete(f"/{task_ids}/")
        self.assertEquals(204, response.status_code)
        self.assertEquals({}, self.get(f"/{task_ids}/"))
