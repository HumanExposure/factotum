from datetime import timedelta
import json
import time


from django.contrib.auth import get_user_model
from django.test import Client, override_settings

from crum import impersonate
from celery_djangotest.unit import TransactionTestCase

from celery_usertask.models import UserTaskLog
from celery_usertask.tests.tasks import task, shadowtask


class TestUserTasks(TransactionTestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create(
            username="test", email="test@test.com", password="test"
        )

    def test_usertasks(self):
        with impersonate(self.user):
            asyncresult = task.delay()
        result = asyncresult.get()
        self.assertEqual(result, self.user.pk)

    def test_resultexpire(self):
        self._app.conf.result_expires = timedelta(seconds=5)
        with impersonate(self.user):
            asyncresult = task.delay()
        asyncresult.get()
        q = UserTaskLog.objects.filter(task=asyncresult.id)
        self.assertTrue(q.exists())
        time.sleep(5)
        self.assertFalse(q.exists())

    def test_name(self):
        with impersonate(self.user):
            asyncresult = task.delay()
        asyncresult.get()
        name = UserTaskLog.objects.get(task=asyncresult.id).name
        self.assertEqual(name, "celery_usertask.tests.tasks.task")

    def test_shadownamekwarg(self):
        with impersonate(self.user):
            asyncresult = task.apply_async(shadow="shadow.name")
        asyncresult.get()
        name = UserTaskLog.objects.get(task=asyncresult.id).name
        self.assertEqual(name, "shadow.name")

    def test_shadownameclass(self):
        with impersonate(self.user):
            asyncresult = shadowtask.delay()
        asyncresult.get()
        name = UserTaskLog.objects.get(task=asyncresult.id).name
        self.assertEqual(name, "shadow.name")

    @override_settings(ROOT_URLCONF="celery_usertask.urls")
    def test_view(self):
        with impersonate(self.user):
            asyncresult = task.delay()
        asyncresult.wait()
        c = Client()
        c.force_login(self.user)
        data = json.loads(c.get("/").content)
        self.assertEqual(
            data, [{"task": asyncresult.id, "name": "celery_usertask.tests.tasks.task"}]
        )
