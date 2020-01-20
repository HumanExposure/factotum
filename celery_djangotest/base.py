import uuid

import celery

from celery.contrib.testing.worker import setup_app_for_worker, start_worker
from celery.contrib.testing.app import setup_default_app, TestApp


class CeleryBaseTestMixin:
    @classmethod
    def setUpClass(cls):
        queue = uuid.uuid4().hex
        cls._app.conf.task_reject_on_worker_lost = True
        cls._app.conf.task_default_queue = queue
        cls._app.conf.task_default_delivery_mode = "transient"
        cls._app.loader.import_module("celery.contrib.testing.tasks")
        setup_app_for_worker(cls._app, None, None)
        cls._worker_context = start_worker(cls._app, queues=queue)
        cls._worker_context.__enter__()
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        cls._worker_context.__exit__(None, None, None)
        super().tearDownClass()


class CeleryUnitTestMixin(CeleryBaseTestMixin):
    @classmethod
    def setUpClass(cls):
        cls._app = TestApp()
        cls._app.autodiscover_tasks()
        cls._app_context = setup_default_app(cls._app)
        cls._app_context.__enter__()
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        cls._app_context.__exit__(None, None, None)
        super().tearDownClass()


class CeleryIntegrationTestMixin(CeleryBaseTestMixin):
    @classmethod
    def setUpClass(cls):
        cls._app = celery.current_app
        super().setUpClass()
