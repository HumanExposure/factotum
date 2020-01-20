import os
import sys

from celery.contrib.testing.worker import setup_app_for_worker, start_worker
from django.utils.autoreload import DJANGO_AUTORELOAD_ENV


class runserverwithcelery:
    def __init__(self, app):
        app.loader.import_module("celery.contrib.testing.tasks")
        setup_app_for_worker(app, None, None)
        self.worker_context = start_worker(app)
        self.worker_on = False

    def __enter__(self):
        if (
            len(sys.argv) > 1
            and sys.argv[1] == "runserver"
            and os.getenv(DJANGO_AUTORELOAD_ENV) == "true"
        ):
            self.worker_context.__enter__()
            self.worker_on = True

    def __exit__(self, exc_type, exc_value, traceback):
        if self.worker_on:
            self.worker_context.__exit__(None, None, None)
